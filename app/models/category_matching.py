# app/models/category_matching.py
from datetime import datetime
from app.extensions import db


class CategoryKeyword(db.Model):
    """โมเดลสำหรับเก็บคำสำคัญที่ใช้ในการจับคู่หมวดหมู่อัตโนมัติ"""
    __tablename__ = 'category_keywords'

    id = db.Column(db.Integer, primary_key=True)
    keyword = db.Column(db.String(100), nullable=False)
    pattern = db.Column(db.String(255), nullable=True)  # สำหรับ regex pattern
    is_regex = db.Column(db.Boolean, default=False)  # บอกว่าเป็น regex หรือคำสำคัญปกติ
    priority = db.Column(db.Integer, default=1)  # ลำดับความสำคัญ (ค่ามากมีความสำคัญสูงกว่า)

    # Foreign keys
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)

    # เพิ่มฟิลด์ว่าใครสร้าง/แก้ไข
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    updated_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    category = db.relationship('Category', backref='keywords')

    def __repr__(self):
        return f'<CategoryKeyword {self.keyword} for {self.category.name}>'


class ImportBatch(db.Model):
    """โมเดลสำหรับเก็บข้อมูลการนำเข้าในแต่ละครั้ง"""
    __tablename__ = 'import_batches'

    id = db.Column(db.Integer, primary_key=True)
    batch_reference = db.Column(db.String(50), unique=True, nullable=False)  # รหัสอ้างอิงการนำเข้า
    source = db.Column(db.String(50), nullable=False)  # แหล่งที่มา เช่น 'SCB', 'KBANK'
    file_name = db.Column(db.String(255), nullable=False)  # ชื่อไฟล์ที่อัพโหลด
    total_records = db.Column(db.Integer, default=0)  # จำนวนรายการทั้งหมด
    imported_records = db.Column(db.Integer, default=0)  # จำนวนรายการที่นำเข้าสำเร็จ
    duplicate_records = db.Column(db.Integer, default=0)  # จำนวนรายการซ้ำที่พบ
    error_records = db.Column(db.Integer, default=0)  # จำนวนรายการที่มีข้อผิดพลาด
    status = db.Column(db.String(20), default='pending')  # 'pending', 'processing', 'completed', 'failed'

    # Foreign keys
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    imported_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime, nullable=True)

    # Relationships
    transactions = db.relationship('Transaction', backref='import_batch',
                                   primaryjoin="Transaction.import_batch_id==ImportBatch.batch_reference",
                                   foreign_keys="Transaction.import_batch_id")

    def __repr__(self):
        return f'<ImportBatch {self.batch_reference} from {self.source}>'


class TransactionCategoryHistory(db.Model):
    """โมเดลสำหรับเก็บประวัติการเลือกหมวดหมู่ เพื่อใช้ในการเรียนรู้"""
    __tablename__ = 'transaction_category_history'

    id = db.Column(db.Integer, primary_key=True)
    description_pattern = db.Column(db.String(255), nullable=False)  # รูปแบบคำอธิบาย
    bank_reference_pattern = db.Column(db.String(100), nullable=True)  # รูปแบบรหัสอ้างอิงธนาคาร
    count = db.Column(db.Integer, default=1)  # จำนวนครั้งที่มีการเลือกหมวดหมู่นี้

    # Foreign keys
    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)

    # Timestamps
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    category = db.relationship('Category', backref='history_matches')

    __table_args__ = (
        db.UniqueConstraint('description_pattern', 'bank_reference_pattern', 'organization_id',
                            name='unique_transaction_pattern'),
    )

    def __repr__(self):
        return f'<TransactionCategoryHistory {self.description_pattern} -> {self.category.name}>'

    @classmethod
    def find_matching_category(cls, description, bank_reference, organization_id):
        """ค้นหาหมวดหมู่ที่น่าจะตรงกับรายการนี้จากประวัติ"""
        from sqlalchemy import or_

        # ค้นหาจากทั้งรายละเอียดและรหัสอ้างอิง (ถ้ามี)
        query = cls.query.filter_by(organization_id=organization_id)

        if bank_reference:
            query = query.filter(or_(
                cls.bank_reference_pattern == bank_reference,
                cls.description_pattern == description
            ))
        else:
            query = query.filter(cls.description_pattern == description)

        # เรียงลำดับตามจำนวนการใช้งาน (มากไปน้อย)
        result = query.order_by(cls.count.desc()).first()

        return result.category_id if result else None

    @classmethod
    def update_history(cls, description, bank_reference, category_id, organization_id):
        """อัปเดตหรือเพิ่มประวัติการจับคู่หมวดหมู่"""
        record = cls.query.filter_by(
            description_pattern=description,
            bank_reference_pattern=bank_reference,
            organization_id=organization_id
        ).first()

        if record:
            # ถ้ามีประวัติอยู่แล้ว และเป็นหมวดหมู่เดิม
            if record.category_id == category_id:
                record.count += 1
            else:
                # ถ้าเปลี่ยนหมวดหมู่ ให้อัปเดตเป็นหมวดหมู่ใหม่และรีเซ็ตจำนวนนับ
                record.category_id = category_id
                record.count = 1
        else:
            # ถ้ายังไม่มีประวัติ ให้สร้างใหม่
            record = cls(
                description_pattern=description,
                bank_reference_pattern=bank_reference,
                category_id=category_id,
                organization_id=organization_id,
                count=1
            )
            db.session.add(record)

        db.session.commit()