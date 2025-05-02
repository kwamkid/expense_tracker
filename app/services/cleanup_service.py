# app/services/cleanup_service.py
import os
import glob
from datetime import datetime
from flask import current_app
import logging


def cleanup_import_files(max_files=3):
    """
    เก็บไฟล์ import เฉพาะที่นำเข้าล่าสุด max_files ไฟล์ ที่เหลือจะถูกลบเพื่อประหยัดพื้นที่

    Args:
        max_files (int): จำนวนไฟล์ล่าสุดที่ต้องการเก็บไว้ (default: 3)

    Returns:
        int: จำนวนไฟล์ที่ถูกลบ
    """
    try:
        # กำหนด path ไปยังโฟลเดอร์ imports
        imports_dir = os.path.join(current_app.static_folder, 'uploads/imports')

        # ตรวจสอบว่าโฟลเดอร์มีอยู่หรือไม่
        if not os.path.exists(imports_dir):
            current_app.logger.warning(f"Import directory not found: {imports_dir}")
            return 0

        # รับรายการไฟล์ทั้งหมดในโฟลเดอร์
        files = glob.glob(os.path.join(imports_dir, '*'))

        # ถ้ามีไฟล์น้อยกว่าหรือเท่ากับจำนวนที่ต้องการเก็บ ไม่ต้องลบอะไร
        if len(files) <= max_files:
            return 0

        # เรียงลำดับไฟล์ตามเวลาที่แก้ไขล่าสุด (เรียงจากใหม่ไปเก่า)
        files.sort(key=os.path.getmtime, reverse=True)

        # เก็บไฟล์ล่าสุด max_files ไฟล์
        files_to_keep = files[:max_files]
        files_to_delete = files[max_files:]

        # ลบไฟล์ที่เหลือ
        deleted_count = 0
        for file_path in files_to_delete:
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    deleted_count += 1
            except Exception as e:
                current_app.logger.error(f"Error deleting file {file_path}: {str(e)}")

        if deleted_count > 0:
            current_app.logger.info(f"Cleanup: deleted {deleted_count} old import files.")

        return deleted_count

    except Exception as e:
        current_app.logger.error(f"Error during import files cleanup: {str(e)}")
        return 0


# เพิ่มเติมในไฟล์ app/services/cleanup_service.py

def cleanup_temp_import_files(hours=24):
    """
    ลบไฟล์ชั่วคราวในโฟลเดอร์ temp_imports ที่มีอายุมากกว่า X ชั่วโมง

    Args:
        hours (int): จำนวนชั่วโมงที่ไฟล์ควรจะถูกเก็บไว้ (default: 24 ชั่วโมง)

    Returns:
        int: จำนวนไฟล์ที่ถูกลบ
    """
    try:
        import time
        from datetime import datetime, timedelta

        # กำหนด path ไปยังโฟลเดอร์ temp_imports
        temp_dir = os.path.join(current_app.static_folder, 'uploads/temp_imports')

        # ตรวจสอบว่าโฟลเดอร์มีอยู่หรือไม่
        if not os.path.exists(temp_dir):
            return 0

        # คำนวณเวลาที่เก่ากว่า X ชั่วโมง
        cutoff_time = time.time() - (hours * 3600)

        # รับรายการไฟล์ทั้งหมดในโฟลเดอร์
        files = glob.glob(os.path.join(temp_dir, '*.*'))

        # ลบไฟล์ที่เก่ากว่า X ชั่วโมง
        deleted_count = 0
        for file_path in files:
            try:
                if os.path.isfile(file_path):
                    file_modified_time = os.path.getmtime(file_path)
                    if file_modified_time < cutoff_time:
                        os.remove(file_path)
                        deleted_count += 1
            except Exception as e:
                current_app.logger.error(f"Error deleting temp file {file_path}: {str(e)}")

        if deleted_count > 0:
            current_app.logger.info(
                f"Cleanup: deleted {deleted_count} temporary import files older than {hours} hours.")

        return deleted_count

    except Exception as e:
        current_app.logger.error(f"Error during temp import files cleanup: {str(e)}")
        return 0