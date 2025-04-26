from flask import Blueprint, request, jsonify, current_app
from werkzeug.utils import secure_filename
from app.services.file_service import save_receipt
from app.services.ocr_service import process_receipt_image
import os

api_bp = Blueprint('api', __name__, url_prefix='/api')


@api_bp.route('/ocr/receipt', methods=['POST'])
def ocr_receipt():
    """
    API endpoint สำหรับประมวลผล OCR ของรูปภาพใบเสร็จ

    ต้องส่งไฟล์รูปภาพในฟอร์มด้วยชื่อฟิลด์ 'receipt'

    Returns:
        JSON response ที่มีข้อมูลที่ดึงได้จากใบเสร็จ
    """
    try:
        if 'receipt' not in request.files:
            return jsonify({'success': False, 'error': 'ไม่พบไฟล์รูปภาพ กรุณาอัพโหลดไฟล์'}), 400

        file = request.files['receipt']

        if file.filename == '':
            return jsonify({'success': False, 'error': 'ไม่ได้เลือกไฟล์ กรุณาเลือกไฟล์ก่อนอัพโหลด'}), 400

        # บันทึกไฟล์
        filename = save_receipt(file)
        if not filename:
            return jsonify({'success': False,
                            'error': 'ประเภทไฟล์ไม่ถูกต้อง รองรับเฉพาะไฟล์รูปภาพ (jpg, jpeg, png, gif) เท่านั้น'}), 400

        # สร้างพาธเต็มของไฟล์
        file_path = os.path.join(
            current_app.root_path,
            current_app.config['UPLOAD_FOLDER'],
            filename
        )

        # ประมวลผล OCR
        extracted_data = process_receipt_image(file_path)

        # เพิ่ม logs สำหรับการดีบัก
        current_app.logger.info(f"OCR results for {filename}: {extracted_data}")

        # ตรวจสอบว่าได้ข้อมูลหรือไม่
        if not extracted_data or all(value is None for value in extracted_data.values()):
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

        return jsonify({
            'success': True,
            'data': extracted_data,
            'filename': filename
        })

    except Exception as e:
        current_app.logger.error(f"Error in OCR processing: {str(e)}")
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