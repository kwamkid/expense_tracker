# app/models/transaction.py
from datetime import datetime
from app.extensions import db


class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)
    transaction_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    type = db.Column(db.String(20), nullable=False)  # 'income' or 'expense'
    status = db.Column(db.String(20), default='completed')  # 'pending' or 'completed'
    receipt_path = db.Column(db.String(255), nullable=True)

    # Foreign keys
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)

    # เพิ่มฟิลด์ว่าใครสร้าง/แก้ไข
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f'<Transaction {self.amount} ({self.type})>'

    # Utility methods
    @classmethod
    def get_monthly_total(cls, organization_id, year, month, transaction_type, status=None):
        """ดึงยอดรวมรายเดือนแยกตามประเภท (รายรับ/รายจ่าย) และสถานะ"""
        from sqlalchemy import func, extract

        query = db.session.query(func.sum(cls.amount)).filter(
            cls.organization_id == organization_id,
            cls.type == transaction_type,
            extract('year', cls.transaction_date) == year,
            extract('month', cls.transaction_date) == month
        )

        if status:
            query = query.filter(cls.status == status)

        return query.scalar() or 0