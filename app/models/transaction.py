# app/models/transaction.py
from datetime import datetime
from app.extensions import db
from sqlalchemy import Index


class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text, nullable=True)
    transaction_date = db.Column(db.Date, nullable=False, default=datetime.utcnow().date)
    type = db.Column(db.String(20), nullable=False)  # 'income' or 'expense'
    status = db.Column(db.String(20), default='completed')  # 'pending' or 'completed'
    receipt_path = db.Column(db.String(255), nullable=True)

    # ฟิลด์ใหม่สำหรับระบบนำเข้าธุรกรรม - เพิ่ม nullable=True สำหรับทุกฟิลด์
    transaction_hash = db.Column(db.String(64), nullable=True)  # ใช้เช็ครายการซ้ำ
    bank_reference = db.Column(db.String(100), nullable=True)  # รหัสอ้างอิงจากธนาคาร (ถ้ามี)
    imported_from = db.Column(db.String(50), nullable=True)  # ชื่อธนาคารที่นำเข้า
    import_batch_id = db.Column(db.String(50), nullable=True)  # รหัสชุดการนำเข้า

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

    # สร้าง index สำหรับ transaction_hash แทนการใช้ index=True ในการประกาศคอลัมน์
    __table_args__ = (
        Index('ix_transaction_hash', 'transaction_hash'),
    )

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

    @classmethod
    def find_duplicate_by_hash(cls, transaction_hash, organization_id):
        """ค้นหาธุรกรรมที่มี hash ตรงกัน (ป้องกันการนำเข้าซ้ำ)"""
        # ตรวจสอบว่าคอลัมน์ transaction_hash มีอยู่ในตาราง
        if hasattr(cls, 'transaction_hash'):
            return cls.query.filter_by(
                transaction_hash=transaction_hash,
                organization_id=organization_id
            ).first()
        return None

    @classmethod
    def find_potential_duplicates(cls, date, amount, organization_id, description=None):
        """ค้นหาธุรกรรมที่อาจซ้ำซ้อนโดยใช้วันที่และจำนวนเงิน"""
        query = cls.query.filter_by(
            transaction_date=date,
            amount=amount,
            organization_id=organization_id
        )

        # ถ้ามีคำอธิบาย ให้ค้นหาแบบคร่าวๆ
        if description:
            from sqlalchemy import or_
            # ค้นหาคำอธิบายที่คล้ายกัน (ดูว่ามีคำอธิบายเดิมอยู่ในคำอธิบายใหม่ หรือกลับกัน)
            query = query.filter(or_(
                cls.description.contains(description),
                description.contains(cls.description)
            ))

        return query.all()