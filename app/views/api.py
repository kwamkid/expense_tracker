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
    if 'receipt' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['receipt']

    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    try:
        # บันทึกไฟล์
        filename = save_receipt(file)
        if not filename:
            return jsonify({'error': 'Invalid file type'}), 400

        # สร้างพาธเต็มของไฟล์
        file_path = os.path.join(
            current_app.root_path,
            current_app.config['UPLOAD_FOLDER'],
            filename
        )

        # ประมวลผล OCR
        extracted_data = process_receipt_image(file_path)

        if not extracted_data:
            return jsonify({'error': 'Failed to extract data from receipt'}), 400

        return jsonify({
            'success': True,
            'data': extracted_data,
            'filename': filename
        })

    except Exception as e:
        current_app.logger.error(f"Error in OCR processing: {str(e)}")
        return jsonify({'error': f'OCR processing failed: {str(e)}'}), 500