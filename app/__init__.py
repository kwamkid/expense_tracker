# app/__init__.py
from flask import Flask
from app.config import Config
from app.extensions import db, migrate, login_manager, csrf
import os


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

    # Ensure uploads directory exists
    os.makedirs(os.path.join(app.static_folder, 'uploads', 'receipts'), exist_ok=True)

    # Initialize extensions
    initialize_extensions(app)

    # Register blueprints
    register_blueprints(app)

    # Register error handlers
    register_error_handlers(app)

    return app


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
    from app.views.api import api_bp  # เพิ่มบรรทัดนี้


    app.register_blueprint(auth_bp)
    app.register_blueprint(dashboard_bp)
    app.register_blueprint(accounts_bp)
    app.register_blueprint(categories_bp)
    app.register_blueprint(transactions_bp)
    app.register_blueprint(reports_bp)
    app.register_blueprint(api_bp)  # เพิ่มบรรทัดนี้



def register_error_handlers(app):
    """Register error handlers"""

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500
