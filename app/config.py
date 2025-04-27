# app/config.py
import os
from datetime import timedelta

class Config:
    """Base config."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-please-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///expense_tracker.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Upload settings - เพิ่มขนาดเป็น 32MB
    MAX_CONTENT_LENGTH = 32 * 1024 * 1024  # 32MB max upload (เดิมเป็น 16MB)
    UPLOAD_FOLDER = 'static/uploads/receipts'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf' , 'heif'}

    # Session settings
    PERMANENT_SESSION_LIFETIME = timedelta(days=14)

    # Flash message settings
    MESSAGE_CATEGORIES = ['success', 'info', 'warning', 'danger']

    # Pagination
    ITEMS_PER_PAGE = 10