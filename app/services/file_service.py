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

def save_receipt(file_data):
    """บันทึกไฟล์ใบเสร็จ"""
    if file_data and allowed_file(file_data.filename):
        try:
            # เพิ่มการบันทึกข้อมูลเพื่อการตรวจสอบ
            current_app.logger.info(f"Saving receipt file: {file_data.filename}, MIME: {file_data.content_type}")

            # สร้างชื่อไฟล์ที่ไม่ซ้ำกัน
            filename = secure_filename(file_data.filename)
            current_app.logger.info(f"Secured filename: {filename}")

            ext = filename.rsplit('.', 1)[1].lower()
            new_filename = f"{uuid.uuid4().hex}_{datetime.now().strftime('%Y%m%d')}.{ext}"
            current_app.logger.info(f"Generated new filename: {new_filename}")

            # กำหนดพาธสำหรับบันทึกไฟล์
            upload_folder = current_app.config['UPLOAD_FOLDER']
            current_app.logger.info(f"Upload folder: {upload_folder}")

            filepath = os.path.join(current_app.root_path, upload_folder, new_filename)
            current_app.logger.info(f"Full filepath: {filepath}")

            # ตรวจสอบว่าโฟลเดอร์มีอยู่จริง
            os.makedirs(os.path.dirname(filepath), exist_ok=True)

            # บันทึกไฟล์
            if ext in ['jpg', 'jpeg', 'png', 'gif']:
                # ถ้าเป็นรูปภาพให้ย่อขนาด
                try:
                    img = Image.open(file_data)
                    width, height = img.size
                    current_app.logger.info(f"Original image size: {width}x{height}")

                    img.thumbnail((800, 800))  # ย่อขนาดรูปให้มีความกว้างหรือความสูงไม่เกิน 800px
                    width, height = img.size
                    current_app.logger.info(f"Resized image size: {width}x{height}")

                    img.save(filepath, quality=85, optimize=True)  # บีบอัดรูปเพื่อลดขนาดไฟล์
                    current_app.logger.info(f"Image saved successfully")

                    # ตรวจสอบว่าไฟล์ถูกบันทึกจริง
                    if os.path.exists(filepath):
                        file_size = os.path.getsize(filepath)
                        current_app.logger.info(f"File saved successfully. Size: {file_size} bytes")
                    else:
                        current_app.logger.error(f"File was not saved: {filepath}")
                        return None

                except Exception as img_error:
                    current_app.logger.error(f"Error processing image: {str(img_error)}")
                    # ถ้าประมวลผลภาพไม่สำเร็จ ให้ลองบันทึกไฟล์โดยตรง
                    file_data.seek(0)  # กลับไปที่จุดเริ่มต้นของไฟล์
                    file_data.save(filepath)
                    current_app.logger.info(f"Saved original file as fallback")
            else:
                # ถ้าเป็นไฟล์อื่นให้บันทึกตามปกติ
                file_data.save(filepath)
                current_app.logger.info(f"Non-image file saved directly")

            # ตรวจสอบอีกครั้งว่าไฟล์ถูกบันทึกจริง
            if os.path.exists(filepath):
                return new_filename
            else:
                current_app.logger.error(f"File was not saved after all attempts: {filepath}")
                return None

        except Exception as e:
            current_app.logger.error(f"Error saving receipt: {str(e)}")
            import traceback
            current_app.logger.error(f"Traceback: {traceback.format_exc()}")
            return None

    else:
        if not file_data:
            current_app.logger.error("Empty file data")
        else:
            current_app.logger.error(f"File not allowed: {file_data.filename}")
        return None


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