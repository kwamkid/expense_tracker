# app/views/api.py
# เพิ่มการ import login_required
from flask import Blueprint, jsonify, request, current_app
from flask_login import login_required, current_user  # เพิ่ม import login_required ตรงนี้
import os
import uuid
import json
from datetime import datetime
from werkzeug.utils import secure_filename
from app.extensions import db  # เพิ่มบรรทัดนี้เพื่อนำเข้า db
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
        organization_id=current_user.active_organization_id
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


# app/views/api.py - แก้ไขฟังก์ชัน update_transaction_status

@api_bp.route('/transactions/update-status', methods=['POST'])
@login_required
def update_transaction_status():
    """API สำหรับอัพเดตสถานะธุรกรรม"""
    from app.models import Transaction, Account

    try:
        transaction_id = request.json.get('id')
        new_status = request.json.get('status')  # 'completed' หรือ 'pending'

        if not transaction_id or not new_status:
            return jsonify({
                'success': False,
                'error': 'Missing required parameters'
            }), 400

        # ค้นหาธุรกรรมพร้อมกับตรวจสอบว่าเป็นของผู้ใช้ปัจจุบัน
        transaction = db.session.query(Transaction).filter(
            Transaction.id == transaction_id,
            Transaction.organization_id == current_user.active_organization_id
        ).first()

        if not transaction:
            return jsonify({
                'success': False,
                'error': 'Transaction not found'
            }), 404

        # บันทึกสถานะเดิมก่อนเปลี่ยน
        old_status = transaction.status

        # ไม่ต้องทำอะไรถ้าสถานะเดิมและใหม่เหมือนกัน
        if old_status == new_status:
            return jsonify({
                'success': True,
                'message': 'Status unchanged',
                'transaction': {
                    'id': transaction.id,
                    'status': transaction.status,
                    'type': transaction.type,
                    'amount': transaction.amount
                }
            })

        # อัพเดตสถานะในฐานข้อมูล
        db.session.begin_nested()  # สร้าง savepoint เพื่อให้สามารถ rollback ได้ถ้าเกิดข้อผิดพลาด

        try:
            # อัพเดตบัญชีตามการเปลี่ยนแปลงสถานะ
            account = Account.query.get(transaction.account_id)

            if not account:
                db.session.rollback()
                return jsonify({
                    'success': False,
                    'error': 'Account not found'
                }), 404

            # ถ้าเปลี่ยนจาก pending เป็น completed
            if old_status == 'pending' and new_status == 'completed':
                if transaction.type == 'income':
                    account.balance += transaction.amount
                else:  # expense
                    account.balance -= transaction.amount

                current_app.logger.info(
                    f"Updating from pending to completed. Account {account.id} balance: {account.balance}")

            # ถ้าเปลี่ยนจาก completed เป็น pending
            elif old_status == 'completed' and new_status == 'pending':
                if transaction.type == 'income':
                    # ตรวจสอบว่าบัญชีมียอดเงินพอหรือไม่
                    if account.balance < transaction.amount:
                        db.session.rollback()
                        return jsonify({
                            'success': False,
                            'error': 'ไม่สามารถเปลี่ยนสถานะได้ เนื่องจากบัญชีมียอดเงินไม่เพียงพอ'
                        }), 400

                    account.balance -= transaction.amount
                else:  # expense
                    account.balance += transaction.amount

                current_app.logger.info(
                    f"Updating from completed to pending. Account {account.id} balance: {account.balance}")

            # เปลี่ยนสถานะธุรกรรม
            transaction.status = new_status

            # บันทึกการเปลี่ยนแปลงทั้งหมด
            db.session.commit()

            return jsonify({
                'success': True,
                'message': f'Transaction status updated to {new_status}',
                'transaction': {
                    'id': transaction.id,
                    'status': transaction.status,
                    'type': transaction.type,
                    'amount': transaction.amount
                },
                'account': {
                    'id': account.id,
                    'name': account.name,
                    'balance': account.balance
                }
            })

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Error updating transaction status: {str(e)}")
            return jsonify({
                'success': False,
                'error': f'Error updating status: {str(e)}'
            }), 500

    except Exception as e:
        current_app.logger.error(f"Unexpected error in update_transaction_status: {str(e)}")
        return jsonify({
            'success': False,
            'error': f'Unexpected error: {str(e)}'
        }), 500



