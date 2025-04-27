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

api_bp = Blueprint('api', __name__, url_prefix='/api')


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


@api_bp.route('/transactions/update-status', methods=['POST'])
@login_required
def update_transaction_status():
    """API สำหรับอัพเดตสถานะธุรกรรม"""
    from app.models import Transaction, Account

    transaction_id = request.json.get('id')
    new_status = request.json.get('status')  # 'completed' หรือ 'pending'

    if not transaction_id or not new_status:
        return jsonify({
            'success': False,
            'error': 'Missing required parameters'
        }), 400

    transaction = Transaction.query.filter_by(id=transaction_id, user_id=current_user.id).first()

    if not transaction:
        return jsonify({
            'success': False,
            'error': 'Transaction not found'
        }), 404

    old_status = transaction.status

    # ไม่ต้องทำอะไรถ้าสถานะเดิมและใหม่เหมือนกัน
    if old_status == new_status:
        return jsonify({
            'success': True,
            'message': 'Status unchanged'
        })

    # อัพเดตสถานะ
    transaction.status = new_status

    # อัพเดตยอดเงินในบัญชี
    account = Account.query.get(transaction.account_id)

    # ถ้าเปลี่ยนจาก pending เป็น completed
    if old_status == 'pending' and new_status == 'completed':
        if transaction.type == 'income':
            account.balance += transaction.amount
        else:  # expense
            account.balance -= transaction.amount

    # ถ้าเปลี่ยนจาก completed เป็น pending
    elif old_status == 'completed' and new_status == 'pending':
        if transaction.type == 'income':
            account.balance -= transaction.amount
        else:  # expense
            account.balance += transaction.amount

    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Transaction status updated to {new_status}',
        'new_balance': account.balance
    })


