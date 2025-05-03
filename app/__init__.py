# app/__init__.py
from flask import Flask, current_app
from flask_login import LoginManager
from flask_migrate import Migrate
from app.config import Config
from app.models import db, User
import os
import time

login_manager = LoginManager()
migrate = Migrate()


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'

    # Create upload folders
    os.makedirs(os.path.join(app.config['UPLOAD_FOLDER'], 'logo'), exist_ok=True)

    # Register blueprints
    from app.routes import auth_bp, main_bp, transactions_bp, imports_bp, settings_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(imports_bp)
    app.register_blueprint(settings_bp)

    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    # Template globals
    @app.context_processor
    def utility_processor():
        from datetime import datetime
        return dict(current_year=datetime.now().year)

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