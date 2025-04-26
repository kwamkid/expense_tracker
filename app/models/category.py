# app/models/category.py
from datetime import datetime
from app.extensions import db


class Category(db.Model):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    type = db.Column(db.String(20), nullable=False)  # 'income' or 'expense'
    color = db.Column(db.String(20), default='#3498db')  # Hex color code
    icon = db.Column(db.String(50), nullable=True)  # Icon name
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Relationships
    transactions = db.relationship('Transaction', backref='category', lazy='dynamic')

    def __init__(self, name, type, color='#3498db', icon=None, user_id=None):
        self.name = name
        self.type = type
        self.color = color
        self.icon = icon
        self.user_id = user_id

    def __repr__(self):
        return f'<Category {self.name} ({self.type})>'