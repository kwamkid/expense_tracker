# app/__init__.py
from flask import Flask, render_template
from app.config import Config
from app.extensions import db, migrate, login_manager, csrf
import os
import logging
from logging.handlers import RotatingFileHandler
import sys


def create_app(config_class=Config):
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_object(config_class)

    # Try to load the instance config if it exists
    try:
        app.config.from_pyfile('config.py')
    except:
        pass

    # Ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # ตั้งค่า logging
    configure_logging(app)

    # Ensure uploads directory exists
    uploads_dir = os.path.join(app.static_folder, 'uploads', 'receipts')
    os.makedirs(uploads_dir, exist_ok=True)
    app.logger.info(f"Uploads directory: {uploads_dir}")

    # ตรวจสอบ Tesseract
    check_tesseract(app)

    # Initialize extensions
    initialize_extensions(app)

    # Register blueprints
    register_blueprints(app)

    # Register error handlers
    register_error_handlers(app)

    # Register context processors
    register_context_processors(app)

    return app


def configure_logging(app):
    """ตั้งค่าระบบ logging"""
    # สร้างโฟลเดอร์สำหรับเก็บ log
    logs_dir = os.path.join(app.root_path, 'logs')
    os.makedirs(logs_dir, exist_ok=True)

    # ตั้งค่าระดับการบันทึก log
    log_level = logging.DEBUG if app.debug else logging.INFO

    # ตั้งค่าการบันทึกลงไฟล์
    file_handler = RotatingFileHandler(
        os.path.join(logs_dir, 'app.log'),
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(log_level)

    # เพิ่ม handler สำหรับแสดงผลในคอนโซล
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    console_handler.setLevel(log_level)

    # กำหนด formatter และ handler ให้กับ app logger
    app.logger.handlers = []
    app.logger.addHandler(file_handler)
    app.logger.addHandler(console_handler)
    app.logger.setLevel(log_level)

    # กำหนดระดับการบันทึก log สำหรับ werkzeug (หลังบ้านของ Flask)
    logging.getLogger('werkzeug').setLevel(logging.INFO)

    app.logger.info('App logging configured')


def check_tesseract(app):
    """ตรวจสอบ Tesseract OCR"""
    try:
        import pytesseract
        import subprocess

        # ตรวจสอบพาธที่เป็นไปได้
        possible_paths = [
            '/opt/homebrew/bin/tesseract',
            '/usr/bin/tesseract',
            '/usr/local/bin/tesseract'
        ]

        tesseract_path = None
        for path in possible_paths:
            if os.path.exists(path):
                tesseract_path = path
                break

        if tesseract_path:
            app.logger.info(f"Found Tesseract at: {tesseract_path}")
            try:
                # ตรวจสอบเวอร์ชันด้วย subprocess
                output = subprocess.check_output([tesseract_path, '--version']).decode('utf-8')
                app.logger.info(f"Tesseract version info: {output.split('\\n')[0]}")
            except Exception as e:
                app.logger.warning(f"Failed to get Tesseract version: {str(e)}")
        else:
            app.logger.warning("Tesseract not found in any of the expected paths")

    except ImportError:
        app.logger.warning("pytesseract module not installed")
    except Exception as e:
        app.logger.warning(f"Error checking Tesseract: {str(e)}")


def initialize_extensions(app):
    """Initialize Flask extensions"""
    db.init_app(app)
    migrate.init_app(app, db)
    csrf.init_app(app)

    # Flask-Login configuration
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    login_manager.login_message_category = 'info'

    @login_manager.user_loader
    def load_user(user_id):
        from app.models import User
        return User.query.get(int(user_id))


def register_blueprints(app):
    """Register Flask blueprints"""
    from app.views.auth import auth_bp
    from app.views.dashboard import dashboard_bp
    from app.views.accounts import accounts_bp
    from app.views.categories import categories_bp
    from app.views.transactions import transactions_bp
    from app.views.reports import reports_bp
    from app.views.api import api_bp


    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(accounts_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(api_bp)


def register_error_handlers(app):
    """Register error handlers"""

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        app.logger.error(f"500 error: {str(e)}")
        return render_template('errors/500.html'), 500


def register_context_processors(app):
    """Register context processors"""

    @app.context_processor
    def inject_now():
        """Make 'now' variable available in all templates"""
        from datetime import datetime
        return {'now': datetime.now()}