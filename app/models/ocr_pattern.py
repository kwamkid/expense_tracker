# app/models/ocr_pattern.py
from datetime import datetime
from app.extensions import db
import json


class OCRPattern(db.Model):
    __tablename__ = 'ocr_patterns'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False)  # ชื่อรูปแบบ เช่น date, amount, vendor
    category = db.Column(db.String(50), nullable=False)  # หมวดหมู่ เช่น basic, thai, receipt_specific
    pattern = db.Column(db.String(500), nullable=False)  # รูปแบบ regex
    description = db.Column(db.String(255), nullable=True)  # คำอธิบาย
    example = db.Column(db.String(255), nullable=True)  # ตัวอย่างข้อความที่ตรงกับรูปแบบ
    is_active = db.Column(db.Boolean, default=True)  # สถานะการใช้งาน
    priority = db.Column(db.Integer, default=0)  # ลำดับความสำคัญ (สูงมีค่ามาก)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # ความสัมพันธ์กับผู้ใช้ (ถ้ามี)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)  # None = system pattern

    def __repr__(self):
        return f'<OCRPattern {self.name} ({self.category})>'

    @staticmethod
    def get_patterns_by_name(name):
        """ดึงรูปแบบทั้งหมดตามชื่อ เรียงตามลำดับความสำคัญ"""
        return OCRPattern.query.filter_by(name=name, is_active=True).order_by(OCRPattern.priority.desc()).all()

    @staticmethod
    def export_to_json():
        """ส่งออกรูปแบบทั้งหมดเป็น JSON"""
        patterns = OCRPattern.query.filter_by(is_active=True).all()
        result = {}

        for pattern in patterns:
            if pattern.name not in result:
                result[pattern.name] = []

            result[pattern.name].append({
                'pattern': pattern.pattern,
                'category': pattern.category,
                'description': pattern.description,
                'example': pattern.example,
                'priority': pattern.priority
            })

        return json.dumps(result, ensure_ascii=False, indent=2)

    @staticmethod
    def import_from_json(json_data):
        """นำเข้ารูปแบบจาก JSON"""
        data = json.loads(json_data)

        for name, patterns in data.items():
            for pattern_data in patterns:
                pattern = OCRPattern(
                    name=name,
                    pattern=pattern_data['pattern'],
                    category=pattern_data.get('category', 'custom'),
                    description=pattern_data.get('description', ''),
                    example=pattern_data.get('example', ''),
                    priority=pattern_data.get('priority', 0),
                    is_active=True
                )
                db.session.add(pattern)

        db.session.commit()