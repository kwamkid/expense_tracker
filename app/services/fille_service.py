# app/services/file_service.py
import os
import uuid
from datetime import datetime
from flask import current_app
from werkzeug.utils import secure_filename
from PIL import Image


def allowed_file(filename):
    """ตรวจสอบว่าไฟล์มีนามสกุลที่อนุญาตหรือไม่"""
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']


def save_receipt(file_data):
    """บันทึกไฟล์ใบเสร็จ"""
    if file_data and allowed_file(file_data.filename):
        # สร้างชื่อไฟล์ที่ไม่ซ้ำกัน
        filename = secure_filename(file_data.filename)
        ext = filename.rsplit('.', 1)[1].lower()
        new_filename = f"{uuid.uuid4().hex}_{datetime.now().strftime('%Y%m%d')}.{ext}"

        # กำหนดพาธสำหรับบันทึกไฟล์
        filepath = os.path.join(current_app.root_path, current_app.config['UPLOAD_FOLDER'], new_filename)

        # บันทึกไฟล์
        if ext in ['jpg', 'jpeg', 'png', 'gif']:
            # ถ้าเป็นรูปภาพให้ย่อขนาด
            img = Image.open(file_data)
            img.thumbnail((800, 800))  # ย่อขนาดรูปให้มีความกว้างหรือความสูงไม่เกิน 800px
            img.save(filepath, quality=85, optimize=True)  # บีบอัดรูปเพื่อลดขนาดไฟล์
        else:
            # ถ้าเป็นไฟล์อื่นให้บันทึกตามปกติ
            file_data.save(filepath)

        return new_filename

    return None


def delete_receipt(filename):
    """ลบไฟล์ใบเสร็จ"""
    try:
        filepath = os.path.join(current_app.root_path, current_app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            return True
    except Exception as e:
        print(f"Error deleting file: {e}")

    return False