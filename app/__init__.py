# app/__init__.py
from flask import Flask, current_app, redirect, url_for, flash, request
from flask_login import LoginManager, current_user
from flask_migrate import Migrate
from app.models import db, User
import os
import time

login_manager = LoginManager()
migrate = Migrate()


def create_app(config_class=None):
    from app.config import Config

    app = Flask(__name__)
    app.config.from_object(config_class or Config)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # กำหนด middleware สำหรับตรวจสอบบริษัทที่ active
    @app.before_request
    def check_active_company():
        # เช็คเฉพาะเมื่อผู้ใช้ล็อกอินแล้ว
        if current_user.is_authenticated:
            # เส้นทางที่ยกเว้นไม่ต้องตรวจสอบบริษัท
            exempt_endpoints = [
                None,  # กรณี static files
                'static',
                'auth.login',
                'auth.logout',
                'auth.callback',
                'auth.select_company',
                'main.index'
            ]

            # ถ้าไม่ได้อยู่ในเส้นทางที่ยกเว้น
            if request.endpoint not in exempt_endpoints and not request.endpoint.startswith('static'):
                # ตรวจสอบว่ามีบริษัทที่ active หรือไม่
                has_active_company = False

                try:
                    from app.models import UserCompany
                    active_company = UserCompany.query.filter_by(
                        user_id=current_user.id,
                        active_company=True
                    ).first()

                    has_active_company = active_company is not None
                except Exception as e:
                    app.logger.error(f"Error checking active company: {e}")

                # ถ้าไม่มีบริษัทที่ active ให้ไปที่หน้าเลือกบริษัท
                if not has_active_company:
                    flash('กรุณาเลือกบริษัทที่ต้องการใช้งาน', 'warning')
                    return redirect(url_for('auth.select_company'))

    # Create upload folders
    # os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'logo'), exist_ok=True)
    # แก้ไขส่วนที่สร้างไดเรกทอรี
    if 'UPLOAD_FOLDER' in app.config:
        # ถ้ามีการกำหนดค่า UPLOAD_FOLDER
        os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'logo'), exist_ok=True)
    else:
        # ถ้าไม่มีการกำหนดค่า UPLOAD_FOLDER ให้กำหนดค่าเริ่มต้น
        app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
        os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'logo'), exist_ok=True)
        print(f"WARNING: UPLOAD_FOLDER not defined in config, using default: {app.config['UPLOAD_FOLDER']}")

    # Register blueprints
    from app.routes import auth_bp, main_bp, transactions_bp, imports_bp, settings_bp, bank_accounts_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(imports_bp)
    app.register_blueprint(settings_bp)
    app.register_blueprint(bank_accounts_bp)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Template globals
    @app.context_processor
    def utility_processor():
        from datetime import datetime

        # ฟังก์ชัน Helper สำหรับดึงบริษัทที่ active
        def get_active_company():
            if current_user.is_authenticated:
                from app.models import UserCompany
                uc = UserCompany.query.filter_by(user_id=current_user.id, active_company=True).first()
                return uc.company if uc else None
            return None

        return dict(
            current_year=datetime.now().year,
            get_active_company=get_active_company
        )

    # Clean temp files
    @app.before_request
    def before_request():
        clean_temp_files()

    return app


def clean_temp_files():
    """ลบไฟล์ชั่วคราวที่เก่าเกิน 1 ชั่วโมง"""
    try:
        upload_folder = current_app.config.get('UPLOAD_FOLDER')
        if upload_folder and os.path.exists(upload_folder):
            now = time.time()
            for filename in os.listdir(upload_folder):
                if filename.startswith('import_') and filename.endswith('.json'):
                    filepath = os.path.join(upload_folder, filename)
                    try:
                        if os.path.getmtime(filepath) < now - 3600:  # 1 hour
                            os.remove(filepath)
                    except OSError:
                        pass  # ไฟล์อาจถูกลบไปแล้วหรือมีปัญหาอื่น
    except Exception as e:
        # ไม่ต้อง raise error เพื่อไม่ให้กระทบการทำงานหลัก
        print(f"Error cleaning temp files: {e}")