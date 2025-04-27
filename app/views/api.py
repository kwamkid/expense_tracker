from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from app.services.file_service import save_receipt
from app.services.ocr_service import process_receipt_image
from app.extensions import csrf  # เพิ่มบรรทัดนี้
import os
import traceback

api_bp = Blueprint('api', __name__, url_prefix='/api')

@csrf.exempt
@api_bp.route('/ocr/receipt', methods=['POST'])
def ocr_receipt():
    """
    API endpoint สำหรับประมวลผล OCR ของรูปภาพใบเสร็จ

    ต้องส่งไฟล์รูปภาพในฟอร์มด้วยชื่อฟิลด์ 'receipt'

    Returns:
        JSON response ที่มีข้อมูลที่ดึงได้จากใบเสร็จ
    """
    try:
        current_app.logger.info(f"OCR API: Starting OCR processing")

        if 'receipt' not in request.files:
            current_app.logger.warning("OCR API: No file in request")
            return jsonify({'success': False, 'error': 'ไม่พบไฟล์รูปภาพ กรุณาอัพโหลดไฟล์'}), 400

        file = request.files['receipt']
        current_app.logger.info(f"OCR API: Received file: {file.filename}")

        if file.filename == '':
            current_app.logger.warning("OCR API: Empty filename")
            return jsonify({'success': False, 'error': 'ไม่ได้เลือกไฟล์ กรุณาเลือกไฟล์ก่อนอัพโหลด'}), 400

        # บันทึกไฟล์
        filename = save_receipt(file)
        if not filename:
            current_app.logger.warning(f"OCR API: Invalid file type: {file.filename}")
            return jsonify({'success': False,
                            'error': 'ประเภทไฟล์ไม่ถูกต้อง รองรับเฉพาะไฟล์รูปภาพ (jpg, jpeg, png, gif) เท่านั้น'}), 400

        current_app.logger.info(f"OCR API: File saved as: {filename}")

        # สร้างพาธเต็มของไฟล์
        file_path = os.path.join(
            current_app.root_path,
            current_app.config['UPLOAD_FOLDER'],
            filename
        )

        # ตรวจสอบว่าไฟล์มีอยู่จริง
        if not os.path.exists(file_path):
            current_app.logger.error(f"OCR API: Saved file not found: {file_path}")
            return jsonify({'success': False, 'error': 'ไฟล์ไม่ถูกบันทึกอย่างถูกต้อง'}), 500

        current_app.logger.info(f"OCR API: Starting OCR processing on {file_path}")

        # ประมวลผล OCR
        try:
            extracted_data = process_receipt_image(file_path)
            current_app.logger.info(f"OCR API: OCR processing completed successfully")
        except Exception as ocr_error:
            current_app.logger.error(f"OCR API: OCR processing error: {str(ocr_error)}")
            current_app.logger.error(f"OCR API: Traceback: {traceback.format_exc()}")
            # ส่งคืนผลลัพธ์ว่าง แทนที่จะเกิดข้อผิดพลาด - ให้ผู้ใช้กรอกข้อมูลเอง
            return jsonify({
                'success': True,
                'warning': f'ไม่สามารถดึงข้อมูลจากใบเสร็จได้ (ข้อผิดพลาด: {str(ocr_error)[:50]}...) กรุณากรอกข้อมูลด้วยตนเอง',
                'data': {
                    'date': None,
                    'total_amount': None,
                    'vendor': None,
                    'receipt_no': None
                },
                'filename': filename
            })

        # ตรวจสอบว่าได้ข้อมูลหรือไม่
        if not extracted_data or all(value is None for value in extracted_data.values()):
            current_app.logger.warning(f"OCR API: No data extracted from receipt")
            return jsonify({
                'success': True,
                'warning': 'ไม่สามารถดึงข้อมูลจากใบเสร็จได้ กรุณากรอกข้อมูลด้วยตนเอง',
                'data': {
                    'date': None,
                    'total_amount': None,
                    'vendor': None,
                    'receipt_no': None
                },
                'filename': filename
            })

        current_app.logger.info(f"OCR API: Extracted data: {extracted_data}")
        return jsonify({
            'success': True,
            'data': extracted_data,
            'filename': filename
        })

    except Exception as e:
        current_app.logger.error(f"OCR API: Critical error in API: {str(e)}")
        # บันทึกแสต็กเทรซเพื่อการดีบัก
        current_app.logger.error(f"OCR API Traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': f'การประมวลผล OCR ล้มเหลว: {str(e)}'}), 500


@api_bp.route('/categories', methods=['GET'])
def get_categories():
    """
    API endpoint สำหรับดึงข้อมูลหมวดหมู่ตามประเภทธุรกรรม

    Query parameters:
        type: ประเภทหมวดหมู่ ('income' หรือ 'expense')

    Returns:
        JSON array ของหมวดหมู่
    """
    from app.models import Category
    from flask_login import current_user

    transaction_type = request.args.get('type', 'expense')

    if transaction_type not in ['income', 'expense']:
        return jsonify({'error': 'ประเภทไม่ถูกต้อง รองรับเฉพาะ income หรือ expense'}), 400

    categories = Category.query.filter_by(
        user_id=current_user.id,
        type=transaction_type
    ).all()

    result = []
    for category in categories:
        result.append({
            'id': category.id,
            'name': category.name,
            'color': category.color,
            'icon': category.icon
        })

    return jsonify(result)