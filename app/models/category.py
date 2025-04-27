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

    # เปลี่ยนจาก user_id เป็น organization_id
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)

    # เพิ่มฟิลด์ว่าใครสร้าง/แก้ไข
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    transactions = db.relationship('Transaction', backref='category', lazy='dynamic')

    def __init__(self, name, type, color='#3498db', icon=None, organization_id=None, created_by=None, updated_by=None):
        self.name = name
        self.type = type
        self.color = color
        self.icon = icon
        self.organization_id = organization_id
        self.created_by = created_by
        self.updated_by = updated_by

    def __repr__(self):
        return f'<Category {self.name} ({self.type})>'