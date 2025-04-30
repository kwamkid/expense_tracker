# app/models/account.py
from datetime import datetime
from app.extensions import db
from sqlalchemy import func


class Account(db.Model):
    __tablename__ = 'accounts'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    balance = db.Column(db.Float, default=0.0)
    is_active = db.Column(db.Boolean, default=True)

    # เพิ่มเลขที่บัญชี
    account_number = db.Column(db.String(20), nullable=True)
    bank_name = db.Column(db.String(100), nullable=True)  # ชื่อธนาคาร

    # เปลี่ยนจาก user_id เป็น organization_id
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)

    # เพิ่มฟิลด์ว่าใครสร้าง/แก้ไข
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    transactions = db.relationship('Transaction', backref='account', lazy='dynamic', cascade='all, delete-orphan')

    def __repr__(self):
        if self.account_number:
            return f'<Account {self.name} ({self.account_number})>'
        return f'<Account {self.name}>'

    def transaction_count(self):
        """ดึงจำนวนธุรกรรมทั้งหมดของบัญชีนี้โดยไม่ใช้ backref"""
        from app.models.transaction import Transaction
        return db.session.query(func.count(Transaction.id)).filter(Transaction.account_id == self.id).scalar() or 0