from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
import pytz

db = SQLAlchemy()
bangkok_tz = pytz.timezone('Asia/Bangkok')


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    line_id = db.Column(db.String(100), unique=True, nullable=False)
    name = db.Column(db.String(100))
    picture_url = db.Column(db.String(255))
    email = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(bangkok_tz))

    # Company settings
    company_name = db.Column(db.String(200))
    company_address = db.Column(db.Text)
    tax_id = db.Column(db.String(20))
    logo_path = db.Column(db.String(255))

    transactions = db.relationship('Transaction', backref='user', lazy=True)


class Category(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(10), nullable=False)  # 'income' or 'expense'
    keywords = db.Column(db.Text)  # Comma-separated keywords for matching
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    transactions = db.relationship('Transaction', backref='category', lazy=True)


class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    transaction_date = db.Column(db.Date, nullable=False)
    type = db.Column(db.String(10), nullable=False)  # 'income' or 'expense'

    # Import tracking
    bank_reference = db.Column(db.String(100))
    import_batch_id = db.Column(db.String(50))

    created_at = db.Column(db.DateTime, default=lambda: datetime.now(bangkok_tz))
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('category.id'), nullable=False)


class InviteToken(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(100), unique=True, nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(bangkok_tz))
    used = db.Column(db.Boolean, default=False)
    used_by = db.Column(db.Integer, db.ForeignKey('user.id'))


class ImportHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    batch_id = db.Column(db.String(50), unique=True, nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    bank_type = db.Column(db.String(50), nullable=False)
    import_date = db.Column(db.DateTime, default=lambda: datetime.now(bangkok_tz))
    transaction_count = db.Column(db.Integer, default=0)
    total_amount = db.Column(db.Float, default=0)
    status = db.Column(db.String(20), default='completed')  # completed, partial, failed
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # เพิ่ม relationship
    user = db.relationship('User', backref=db.backref('import_histories', lazy=True))