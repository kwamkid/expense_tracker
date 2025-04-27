# app/services/file_service.py
import os
import uuid
from datetime import datetime
from flask import current_app
from werkzeug.utils import secure_filename
from PIL import Image


# app/services/file_service.py
# แก้ไขฟังก์ชัน allowed_file

def allowed_file(filename):
    """ตรวจสอบว่าไฟล์มีนามสกุลที่อนุญาตหรือไม่"""
    if not filename:
        return False

    # เพิ่มการตรวจสอบว่ามี . หรือไม่
    if '.' not in filename:
        return False

    ext = filename.rsplit('.', 1)[1].lower()
    return ext in current_app.config['ALLOWED_EXTENSIONS']


def save_receipt(file):
    """บันทึกไฟล์ใบเสร็จและคืนค่าชื่อไฟล์"""
    filename = secure_filename(file.filename)
    extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

    # สร้างชื่อไฟล์ใหม่
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    new_filename = f"receipt_{timestamp}_{uuid.uuid4().hex[:8]}"

    # ตรวจสอบว่าเป็นไฟล์ HEIC หรือไม่
    if extension in ['heic', 'heif']:
        # แปลง HEIC เป็น JPEG
        try:
            from pillow_heif import register_heif_opener
            register_heif_opener()

            from PIL import Image
            import io

            # อ่านไฟล์
            file_data = file.read()
            image = Image.open(io.BytesIO(file_data))

            # บันทึกเป็น JPEG
            jpeg_filename = f"{new_filename}.jpg"
            jpeg_path = os.path.join(current_app.config['UPLOAD_FOLDER'], jpeg_filename)
            image.save(jpeg_path, format="JPEG", quality=95)

            return jpeg_filename
        except Exception as e:
            current_app.logger.error(f"Error converting HEIC: {str(e)}")
            # กรณีแปลงไม่ได้ให้ใช้วิธีเดิม

    # บันทึกไฟล์ปกติ (ไม่ใช่ HEIC)
    saved_filename = f"{new_filename}.{extension}" if extension else f"{new_filename}"
    file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], saved_filename)

    # ตรวจสอบว่าโฟลเดอร์มีอยู่หรือไม่
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # บันทึกไฟล์
    file.seek(0)  # ย้อนกลับไปที่ต้นไฟล์ (กรณีที่มีการอ่านไฟล์ก่อนหน้านี้)
    file.save(file_path)

    return saved_filename


def delete_receipt(filename):
    """ลบไฟล์ใบเสร็จ"""
    try:
        filepath = os.path.join(current_app.root_path, current_app.config['UPLOAD_FOLDER'], filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            current_app.logger.info(f"Receipt file deleted: {filename}")
            return True
        else:
            current_app.logger.warning(f"Receipt file not found for deletion: {filename}")
    except Exception as e:
        current_app.logger.error(f"Error deleting receipt file: {e}")

    return False