# app/config.py
import os
from datetime import timedelta
from dotenv import load_dotenv
import re

# Load environment variables from .env file
load_dotenv()


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')

    # ตรวจสอบสภาพแวดล้อม
    ENVIRONMENT = os.environ.get('FLASK_ENV', 'development')

    # แก้ไขการตั้งค่า DATABASE_URL เพื่อรองรับ MySQL ที่มีพารามิเตอร์ ssl_mode
    if os.environ.get('DATABASE_URL'):
        database_url = os.environ.get('DATABASE_URL')
        # ตรวจสอบว่าเป็น MySQL และมี ssl_mode
        if 'mysql' in database_url and 'ssl_mode=' in database_url:
            # ดักจับพารามิเตอร์ ssl_mode และลบออก
            # แยกเป็นส่วนฐาน URL และส่วนพารามิเตอร์
            if '?' in database_url:
                base_url, params_string = database_url.split('?', 1)
                # แยกพารามิเตอร์เป็นรายการ
                params = params_string.split('&')
                # กรองพารามิเตอร์ ssl_mode ออก
                filtered_params = [p for p in params if not p.startswith('ssl_mode=')]
                # สร้าง URL ใหม่
                if filtered_params:
                    SQLALCHEMY_DATABASE_URI = base_url + '?' + '&'.join(filtered_params)
                else:
                    SQLALCHEMY_DATABASE_URI = base_url
            else:
                # กรณีที่ไม่มีเครื่องหมาย ? ในลิงก์ (ไม่น่าเป็นไปได้ แต่เผื่อไว้)
                SQLALCHEMY_DATABASE_URI = database_url
        else:
            # ใช้ URL เดิมถ้าไม่ใช่ MySQL หรือไม่มี ssl_mode
            SQLALCHEMY_DATABASE_URI = database_url
    else:
        # ถ้าไม่มี DATABASE_URL ใน environment ให้ใช้ค่า default
        SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://agd_user:MKthailand47@localhost/expense_tracker'

    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # แก้ไขเพิ่มเติมการตั้งค่า MySQL connection
    if 'mysql' in SQLALCHEMY_DATABASE_URI:
        # ตั้งค่า pool options สำหรับ MySQL
        SQLALCHEMY_ENGINE_OPTIONS = {
            'pool_size': 10,
            'pool_recycle': 60,
            'pool_pre_ping': True,
            # ลบพารามิเตอร์ ssl_mode
            'connect_args': {}
        }
    else:
        # ค่า default สำหรับฐานข้อมูลอื่นๆ
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