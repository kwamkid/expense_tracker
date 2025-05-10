# app/config.py
import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')

    # ตรวจสอบสภาพแวดล้อม
    ENVIRONMENT = os.environ.get('FLASK_ENV', 'development')

    # ถ้ามีการตั้งค่า DATABASE_URL ให้ใช้ค่านั้น (สำหรับ production)
    # ถ้าไม่มี ให้ใช้การเชื่อมต่อ local (สำหรับ development)
    if os.environ.get('DATABASE_URL'):
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL')
    else:
        SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://agd_user:MKthailand47@localhost/expense_tracker'

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # ตั้งค่า pool options สำหรับ MySQL
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 60,
        'pool_pre_ping': True,
    }

    # LINE Login
    LINE_CHANNEL_ID = os.environ.get('LINE_CHANNEL_ID')
    LINE_CHANNEL_SECRET = os.environ.get('LINE_CHANNEL_SECRET')
    LINE_REDIRECT_URI = os.environ.get('LINE_REDIRECT_URI')

    # File upload
    UPLOAD_FOLDER = 'app/static/uploads'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'xlsx', 'xls'}

    # Session
    PERMANENT_SESSION_LIFETIME = timedelta(days=7)

    # Timezone
    TIMEZONE = 'Asia/Bangkok'