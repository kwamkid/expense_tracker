# app/routes/__init__.py
from .auth import auth_bp
from .main import main_bp
from .transactions import transactions_bp
from .imports import imports_bp
from .settings import settings_bp

__all__ = ['auth_bp', 'main_bp', 'transactions_bp', 'imports_bp', 'settings_bp']