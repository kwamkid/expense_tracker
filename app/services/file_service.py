# app/services/file_service.py
import os
import uuid
from datetime import datetime
from werkzeug.utils import secure_filename
from PIL import Image
from flask import current_app


def allowed_file(filename):
    """ตรวจสอบว่าไฟล์มีนามสกุลที่อนุญาตหรือไม่"""
    if not filename:
        return False
    if '.' not in filename:
        return False
    ext = filename.rsplit('.', 1)[1].lower()
    return ext in current_app.config['ALLOWED_EXTENSIONS']


def save_receipt(file):
    """บันทึกไฟล์ใบเสร็จ ย่อขนาด และคืนค่าชื่อไฟล์"""
    if not file:
        return None

    # สร้างชื่อไฟล์ใหม่
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    filename = secure_filename(file.filename)
    extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'jpg'
    new_filename = f"receipt_{timestamp}_{uuid.uuid4().hex[:8]}.{extension}"

    # กำหนดพาธสำหรับบันทึกไฟล์
    upload_folder = os.path.join(current_app.root_path, 'static/uploads/receipts')
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, new_filename)

    try:
        # บันทึกไฟล์ต้นฉบับชั่วคราว
        file.save(file_path)

        # ย่อขนาดภาพ (เฉพาะไฟล์รูปภาพ)
        if extension.lower() in ['jpg', 'jpeg', 'png', 'gif']:
            # ขนาดสูงสุดที่ต้องการ
            MAX_SIZE = (1200, 1200)

            # เปิดและย่อขนาดภาพ
            img = Image.open(file_path)
            img.thumbnail(MAX_SIZE, Image.LANCZOS)

            # บันทึกภาพที่ย่อแล้ว
            img.save(file_path, optimize=True, quality=85)

        return new_filename
    except Exception as e:
        # ถ้าเกิดข้อผิดพลาด ลบไฟล์ที่อัพโหลดไปแล้ว (ถ้ามี)
        if os.path.exists(file_path):
            os.remove(file_path)
        return None


def delete_receipt(filename):
    """ลบไฟล์ใบเสร็จ"""
    if not filename:
        return False

    filepath = os.path.join(current_app.root_path, 'static/uploads/receipts', filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        return True
    return False