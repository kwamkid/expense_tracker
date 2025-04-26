# app/config.py
import os
from datetime import timedelta


class Config:
    """Base config."""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-key-please-change-in-production')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///expense_tracker.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Upload settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload
    UPLOAD_FOLDER = 'static/uploads/receipts'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf'}

    # Session settings
    PERMANENT_SESSION_LIFETIME = timedelta(days=14)

    # Flash message settings
    MESSAGE_CATEGORIES = ['success', 'info', 'warning', 'danger']

    # Pagination
    ITEMS_PER_PAGE = 10