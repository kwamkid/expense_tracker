# app/__init__.py
import os
import logging
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

# ตั้งค่าการบันทึกล็อก
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# สร้างอ็อบเจกต์ของ extension ต่างๆ
db = SQLAlchemy()
migrate = Migrate()
login_manager = LoginManager()
login_manager.login_view = 'auth.login'


def create_app():
    """Initialize the Flask application."""
    app = Flask(__name__)

    # บันทึกข้อมูลการเริ่มต้นแอป
    logger.info("Starting application...")

    try:
        # Load configuration
        from app.config import Config
        app.config.from_object(Config)
        logger.info("Configuration loaded successfully")

        # ตรวจสอบค่า UPLOAD_FOLDER
        if 'UPLOAD_FOLDER' not in app.config:
            app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
            logger.warning(f"UPLOAD_FOLDER not defined in config, using default: {app.config['UPLOAD_FOLDER']}")

        # พยายามสร้างไดเรกทอรีสำหรับอัปโหลดไฟล์
        try:
            upload_dir = app.config['UPLOAD_FOLDER']
            logo_dir = os.path.join(upload_dir, 'logo')

            # ตรวจสอบสภาพแวดล้อม
            is_digitalocean = 'DIGITALOCEAN' in os.environ or 'DO_APP_ID' in os.environ

            if not is_digitalocean:
                # ถ้าไม่ได้อยู่บน Digital Ocean ให้สร้างไดเรกทอรีตามปกติ
                os.makedirs(upload_dir, exist_ok=True)
                os.makedirs(logo_dir, exist_ok=True)
                logger.info(f"Created upload directories: {upload_dir}, {logo_dir}")
            else:
                # ถ้าอยู่บน Digital Ocean ให้ใช้ /tmp แทน
                app.config['UPLOAD_FOLDER'] = '/tmp/uploads'
                tmp_logo_dir = os.path.join('/tmp/uploads', 'logo')
                os.makedirs('/tmp/uploads', exist_ok=True)
                os.makedirs(tmp_logo_dir, exist_ok=True)
                logger.info(f"Using temporary upload directory on Digital Ocean: {app.config['UPLOAD_FOLDER']}")
        except Exception as e:
            logger.warning(f"Could not create upload directories: {str(e)}")
            # ยังคงทำงานต่อไปแม้จะไม่สามารถสร้างไดเรกทอรีได้

        # Initialize extensions
        db.init_app(app)
        migrate.init_app(app, db)
        login_manager.init_app(app)
        logger.info("Extensions initialized successfully")

        # Register blueprints
        from app.routes.auth import auth_bp
        from app.routes.main import main_bp
        from app.routes.admin import admin_bp

        app.register_blueprint(auth_bp)
        app.register_blueprint(main_bp)
        app.register_blueprint(admin_bp)
        logger.info("Blueprints registered successfully")

        # ลงทะเบียนฟังก์ชันช่วยเหลือที่ใช้ในเทมเพลต
        from app.utils.helpers import format_date, format_currency
        app.jinja_env.filters['format_date'] = format_date
        app.jinja_env.filters['format_currency'] = format_currency

        # สร้างตารางในฐานข้อมูลในครั้งแรกที่แอปเริ่มทำงาน (ถ้ายังไม่มี)
        with app.app_context():
            try:
                from app.models import User, Location  # นำเข้าโมเดลที่จำเป็น
                # ตรวจสอบว่าตารางมีอยู่หรือไม่ ก่อนที่จะสร้าง
                inspector = db.inspect(db.engine)
                tables = inspector.get_table_names()

                if not tables or 'user' not in tables:
                    logger.info("No tables found in database. Creating tables...")
                    db.create_all()
                    logger.info("Tables created successfully!")
                else:
                    logger.info(f"Database already contains tables: {', '.join(tables)}")
            except Exception as e:
                logger.error(f"Error checking/creating database tables: {str(e)}")
                # ยังคงทำงานต่อไปแม้จะไม่สามารถสร้างตารางได้

        # ลงทะเบียน error handlers
        @app.errorhandler(404)
        def page_not_found(error):
            return "Page not found", 404

        @app.errorhandler(500)
        def internal_server_error(error):
            logger.error(f"Internal server error: {str(error)}")
            return "Internal server error", 500

        # เพิ่ม route สำหรับตรวจสอบสถานะ
        @app.route('/health')
        def health_check():
            return "OK", 200

        # ตรวจสอบการเชื่อมต่อฐานข้อมูล (ใช้ route แทน before_first_request)
        @app.route('/check-db')
        def check_db():
            try:
                db.session.execute("SELECT 1")
                return "Database connection successful!", 200
            except Exception as e:
                logger.error(f"Database connection error: {str(e)}")
                return f"Database connection error: {str(e)}", 500

        logger.info("Application setup complete")
        return app

    except Exception as e:
        logger.error(f"Error in application initialization: {str(e)}")
        # สร้างแอปขั้นต่ำหากมีข้อผิดพลาดในการตั้งค่า
        minimal_app = Flask(__name__)

        @minimal_app.route('/')
        def error_page():
            return f"Application startup error: {str(e)}", 500

        return minimal_app