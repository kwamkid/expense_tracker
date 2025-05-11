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

    # ตรวจสอบและแก้ไข DATABASE_URL ให้ใช้กับ PyMySQL
    if os.environ.get('DATABASE_URL'):
        database_url = os.environ.get('DATABASE_URL')

        # แปลง mysql:// เป็น mysql+pymysql:// ถ้าจำเป็น
        if database_url.startswith('mysql://'):
            database_url = database_url.replace('mysql://', 'mysql+pymysql://', 1)
            print(f"INFO: Converted DATABASE_URL to use pymysql: {database_url}")

        # จัดการกับ ssl_mode
        if 'ssl_mode=' in database_url:
            # แยก URL และพารามิเตอร์
            url_parts = database_url.split('?', 1)
            base_url = url_parts[0]

            # ลบพารามิเตอร์ ssl_mode
            if len(url_parts) > 1:
                params = url_parts[1].split('&')
                filtered_params = [p for p in params if not p.startswith('ssl_mode=')]

                if filtered_params:
                    database_url = base_url + '?' + '&'.join(filtered_params)
                else:
                    database_url = base_url

            print(f"INFO: Removed ssl_mode from DATABASE_URL: {database_url}")

        SQLALCHEMY_DATABASE_URI = database_url
    else:
        # ถ้าไม่มี DATABASE_URL ใน environment ให้ใช้ค่า default
        SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://agd_user:MKthailand47@localhost/expense_tracker'

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # กำหนดค่า engine options สำหรับ MySQL
    if 'mysql' in SQLALCHEMY_DATABASE_URI:
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_size': 10,
            'pool_recycle': 60,
            'pool_pre_ping': True,
            'connect_args': {
                'ssl': {'ssl': True} if 'ondigitalocean.com' in SQLALCHEMY_DATABASE_URI else {}
            }
        }
    else:
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_size': 10,
            'pool_recycle': 60,
            'pool_pre_ping': True,
        }

    # เพิ่มการตั้งค่า UPLOAD_FOLDER
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'app', 'static',
                                 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'xlsx', 'xls'}