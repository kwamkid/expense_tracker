# app/views/api.py
# เพิ่มการ import login_required
from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user  # เพิ่ม import login_required ตรงนี้
import os
import uuid
import json
from datetime import datetime
from werkzeug.utils import secure_filename

from app.services.file_service import allowed_file, save_receipt
from app.services.ocr_service import process_receipt_image

api_bp = Blueprint('api', __name__, url_prefix='/api')


# แก้ไขใน app/views/api.py
# ค้นหาฟังก์ชัน ocr_receipt และแก้ไขส่วนของการตรวจสอบไฟล์

@api_bp.route('/ocr/receipt', methods=['POST'])
# @login_required
def ocr_receipt():
    """API สำหรับอัปโหลดใบเสร็จและวิเคราะห์ด้วย OCR"""
    # เพิ่มการบันทึกข้อมูลเพื่อการดีบัก
    current_app.logger.info(f"OCR API request received: {request.files}")
    current_app.logger.info(f"Request headers: {request.headers}")

    if 'receipt' not in request.files:
        current_app.logger.error("OCR API: No receipt file in request")
        return jsonify({
            'success': False,
            'error': 'ไม่พบไฟล์รูปภาพใบเสร็จ'
        }), 400

    file = request.files['receipt']
    if not file or file.filename == '':
        current_app.logger.error("OCR API: Empty filename")
        return jsonify({
            'success': False,
            'error': 'ไม่ได้เลือกไฟล์'
        }), 400

    if not allowed_file(file.filename):
        current_app.logger.error(f"OCR API: Invalid file type: {file.filename}")
        return jsonify({
            'success': False,
            'error': 'ไฟล์ไม่ถูกต้อง กรุณาอัปโหลดไฟล์รูปภาพ (jpg, jpeg, png, etc.)'
        }), 400

    try:
        # บันทึกไฟล์ชั่วคราวและดำเนินการต่อ...
        # (ส่วนที่เหลือของฟังก์ชันให้คงเดิม)
        # บันทึกไฟล์ชั่วคราว
        upload_folder = os.path.join(current_app.root_path, 'static/uploads/receipts')
        os.makedirs(upload_folder, exist_ok=True)

        # ใช้ UUID สำหรับชื่อไฟล์
        temp_filename = f"{uuid.uuid4().hex}_{datetime.now().strftime('%Y%m%d')}.jpg"
        temp_filepath = os.path.join(upload_folder, temp_filename)

        # บันทึกไฟล์
        file.save(temp_filepath)

        # บันทึก log เพื่อการตรวจสอบ
        current_app.logger.info(f"Saved receipt image to: {temp_filepath}")

        # ประมวลผล OCR
        current_app.logger.info("Starting OCR processing")
        ocr_data = process_receipt_image(temp_filepath)
        current_app.logger.info(f"OCR processing complete. Data: {json.dumps(ocr_data, ensure_ascii=False)}")

        # ถ้ามีข้อมูล receipt_number ให้ใช้อันนั้น แต่ถ้าไม่มีและมี receipt_no ให้ใช้ receipt_no แทน
        if 'receipt_number' in ocr_data and ocr_data['receipt_number']:
            receipt_no = ocr_data['receipt_number']
        elif 'receipt_no' in ocr_data and ocr_data['receipt_no']:
            receipt_no = ocr_data['receipt_no']
        else:
            receipt_no = None

        # สร้างข้อมูลตอบกลับ
        response_data = {
            'date': ocr_data.get('date'),
            'total_amount': ocr_data.get('total_amount'),
            'vendor': ocr_data.get('vendor'),
            'receipt_no': receipt_no,
            'items': ocr_data.get('items', []),
            'ocr_text': ocr_data.get('text', '')  # เพิ่มส่วนนี้
        }

        # บันทึกข้อมูลดิบเพื่อการวิเคราะห์
        log_dir = os.path.join(current_app.root_path, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        log_file_path = os.path.join(log_dir, f'ocr_api_response_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json')
        with open(log_file_path, 'w', encoding='utf-8') as f:
            f.write(json.dumps({
                'original_data': ocr_data,
                'response_data': response_data
            }, ensure_ascii=False, indent=2))
        current_app.logger.info(f"Saved API response log to: {log_file_path}")

        # ตรวจสอบว่ามีข้อมูลหรือไม่
        if all(v is None for v in [response_data['date'], response_data['total_amount'], response_data['vendor'],
                                   response_data['receipt_no']]):
            current_app.logger.warning("No data extracted from receipt")
            return jsonify({
                'success': True,
                'warning': 'ไม่สามารถดึงข้อมูลจากใบเสร็จได้ กรุณากรอกข้อมูลด้วยตนเอง',
                'data': response_data,
                'temp_file': temp_filename
            })

        current_app.logger.info(f"OCR API returning success with data: {json.dumps(response_data, ensure_ascii=False)}")
        return jsonify({
            'success': True,
            'data': response_data,
            'temp_file': temp_filename
        })

    except Exception as e:
        current_app.logger.error(f"Error in OCR API: {str(e)}")
        import traceback
        current_app.logger.error(f"Traceback: {traceback.format_exc()}")

        return jsonify({
            'success': False,
            'error': f'เกิดข้อผิดพลาดในการประมวลผล: {str(e)}'
        }), 500


@api_bp.route('/categories', methods=['GET'])
@login_required
def get_categories():
    """API สำหรับดึงรายการหมวดหมู่ตามประเภท (รายรับ/รายจ่าย)"""
    from app.models import Category

    transaction_type = request.args.get('type', 'expense')  # ค่าเริ่มต้นคือ expense

    # ตรวจสอบว่าประเภทธุรกรรมถูกต้อง
    if transaction_type not in ['income', 'expense']:
        return jsonify({
            'success': False,
            'error': 'Invalid transaction type. Must be "income" or "expense"'
        }), 400

    # ดึงรายการหมวดหมู่
    categories = Category.query.filter_by(
        type=transaction_type,
        user_id=current_user.id
    ).order_by(Category.name).all()

    # สร้างรายการหมวดหมู่
    result = []
    for category in categories:
        result.append({
            'id': category.id,
            'name': category.name,
            'color': category.color,
            'icon': category.icon
        })

    # คืนค่ากลับเป็น JSON
    return jsonify(result)


