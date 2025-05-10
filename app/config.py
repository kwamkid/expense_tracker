# app/config.py
import os
from datetime import timedelta
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///expense_tracker.db')
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL',
    #                                          'mysql+pymysql://username:password@localhost/expense_tracker')

    SQLALCHEMY_TRACK_MODIFICATIONS = False

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