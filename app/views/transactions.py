# app/views/transactions.py
import os
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.forms.transaction import TransactionForm
from app.models import Transaction, Account, Category
from app.services.file_service import save_receipt, delete_receipt
from app.extensions import db

transactions_bp = Blueprint('transactions', __name__, url_prefix='/transactions')


@transactions_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    per_page = current_app.config['ITEMS_PER_PAGE']

    # Filter params
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    transaction_type = request.args.get('type')
    category_id = request.args.get('category_id')
    account_id = request.args.get('account_id')
    status = request.args.get('status')

    query = Transaction.query.filter_by(user_id=current_user.id)

    # Apply filters
    if status:
        query = query.filter_by(status=status)
    if start_date:
        query = query.filter(Transaction.transaction_date >= start_date)
    if end_date:
        query = query.filter(Transaction.transaction_date <= end_date)
    if transaction_type:
        query = query.filter_by(type=transaction_type)
    if category_id:
        query = query.filter_by(category_id=category_id)
    if account_id:
        query = query.filter_by(account_id=account_id)

    # Order by date descending
    query = query.order_by(Transaction.transaction_date.desc())

    # Pagination
    transactions = query.paginate(page=page, per_page=per_page)

    # Get categories and accounts for filter dropdowns
    categories = Category.query.filter_by(user_id=current_user.id).all()
    accounts = Account.query.filter_by(user_id=current_user.id).all()

    return render_template(
        'transactions/index.html',
        transactions=transactions,
        categories=categories,
        accounts=accounts,
        title='รายการธุรกรรม'
    )


# แก้ไขฟังก์ชัน create ใน app/views/transactions.py
@transactions_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    # รับค่า type จาก query string (ถ้ามี)
    transaction_type = request.args.get('type', None)

    form = TransactionForm()

    # กำหนดค่าเริ่มต้นของประเภทธุรกรรมจาก query string
    if transaction_type and transaction_type in ['income', 'expense']:
        form.type.data = transaction_type

    # ดึงบัญชีและหมวดหมู่ของผู้ใช้สำหรับตัวเลือกในฟอร์ม
    form.account_id.choices = [(a.id, a.name) for a in Account.query.filter_by(user_id=current_user.id).all()]

    # ตัวเลือกหมวดหมู่จะเปลี่ยนตามประเภทธุรกรรม (รายรับ/รายจ่าย)
    current_type = form.type.data or transaction_type or 'expense'
    if current_type == 'income':
        form.category_id.choices = [(c.id, c.name) for c in
                                    Category.query.filter_by(user_id=current_user.id, type='income').all()]
    else:
        form.category_id.choices = [(c.id, c.name) for c in
                                    Category.query.filter_by(user_id=current_user.id, type='expense').all()]

    if form.validate_on_submit():
        # สร้างธุรกรรมใหม่
        transaction = Transaction(
            amount=form.amount.data,
            description=form.description.data,
            transaction_date=form.transaction_date.data,
            type=form.type.data,
            status=form.status.data,
            user_id=current_user.id,
            account_id=form.account_id.data,
            category_id=form.category_id.data
        )

        # อัพโหลดใบเสร็จ (ถ้ามี)
        if form.receipt.data:
            receipt_path = save_receipt(form.receipt.data)
            transaction.receipt_path = receipt_path

        db.session.add(transaction)

        # อัพเดทยอดเงินในบัญชี (เฉพาะกรณีสถานะเป็น 'completed')
        if form.status.data == 'completed':
            account = Account.query.get(form.account_id.data)
            if form.type.data == 'income':
                account.balance += form.amount.data
            else:
                account.balance -= form.amount.data

        db.session.commit()
        flash('บันทึกธุรกรรมสำเร็จ!', 'success')
        return redirect(url_for('transactions.index'))

    # ตั้งค่าเริ่มต้นให้ status เป็น 'pending'
    if request.method == 'GET':
        form.status.data = 'pending'

    # ตั้งชื่อหน้าตามประเภทธุรกรรม
    if transaction_type == 'income':
        title = 'เพิ่มรายได้'
    elif transaction_type == 'expense':
        title = 'เพิ่มรายจ่าย'
    else:
        title = 'เพิ่มธุรกรรมใหม่'

    return render_template('transactions/create.html', form=form, title=title, transaction_type=transaction_type)


@transactions_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    transaction = Transaction.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    # เก็บค่าเดิมไว้เพื่อคำนวณยอดเงินในบัญชี
    old_amount = transaction.amount
    old_type = transaction.type
    old_account_id = transaction.account_id
    old_status = transaction.status

    form = TransactionForm(obj=transaction)

    # ดึงบัญชีและหมวดหมู่ของผู้ใช้สำหรับตัวเลือกในฟอร์ม
    form.account_id.choices = [(a.id, a.name) for a in Account.query.filter_by(user_id=current_user.id).all()]

    # ตัวเลือกหมวดหมู่จะเปลี่ยนตามประเภทธุรกรรม (รายรับ/รายจ่าย)
    if form.type.data == 'income':
        form.category_id.choices = [(c.id, c.name) for c in
                                    Category.query.filter_by(user_id=current_user.id, type='income').all()]
    else:
        form.category_id.choices = [(c.id, c.name) for c in
                                    Category.query.filter_by(user_id=current_user.id, type='expense').all()]

    if form.validate_on_submit():
        # อัพเดทข้อมูลธุรกรรม
        transaction.amount = form.amount.data
        transaction.description = form.description.data
        transaction.transaction_date = form.transaction_date.data
        transaction.type = form.type.data
        transaction.status = form.status.data
        transaction.account_id = form.account_id.data
        transaction.category_id = form.category_id.data

        # อัพโหลดใบเสร็จใหม่ (ถ้ามี)
        if form.receipt.data:
            # ลบไฟล์เดิม (ถ้ามี)
            if transaction.receipt_path:
                delete_receipt(transaction.receipt_path)

            # บันทึกไฟล์ใหม่
            receipt_path = save_receipt(form.receipt.data)
            transaction.receipt_path = receipt_path

        # คำนวณและอัพเดทยอดเงินในบัญชี

        # กรณีธุรกรรมเดิมเป็น completed ให้คืนยอดเงิน
        if old_status == 'completed':
            # ถ้าบัญชีเดิมกับบัญชีใหม่เป็นบัญชีเดียวกัน
            if old_account_id == transaction.account_id:
                account = Account.query.get(transaction.account_id)

                # ย้อนคืนธุรกรรมเดิม
                if old_type == 'income':
                    account.balance -= old_amount
                else:
                    account.balance += old_amount

                # เพิ่มธุรกรรมใหม่ (เฉพาะถ้าสถานะยังเป็น completed)
                if transaction.status == 'completed':
                    if transaction.type == 'income':
                        account.balance += transaction.amount
                    else:
                        account.balance -= transaction.amount

            # ถ้าบัญชีเดิมกับบัญชีใหม่เป็นคนละบัญชี
            else:
                # อัพเดทบัญชีเดิม
                old_account = Account.query.get(old_account_id)
                if old_type == 'income':
                    old_account.balance -= old_amount
                else:
                    old_account.balance += old_amount

                # อัพเดทบัญชีใหม่ (เฉพาะถ้าสถานะเป็น completed)
                if transaction.status == 'completed':
                    new_account = Account.query.get(transaction.account_id)
                    if transaction.type == 'income':
                        new_account.balance += transaction.amount
                    else:
                        new_account.balance -= transaction.amount

        # กรณีธุรกรรมเดิมเป็น pending แต่ธุรกรรมใหม่เป็น completed
        elif transaction.status == 'completed':
            account = Account.query.get(transaction.account_id)
            if transaction.type == 'income':
                account.balance += transaction.amount
            else:
                account.balance -= transaction.amount

        db.session.commit()
        flash('แก้ไขธุรกรรมสำเร็จ!', 'success')
        return redirect(url_for('transactions.index'))

    return render_template('transactions/edit.html', form=form, transaction=transaction, title='แก้ไขธุรกรรม')


@transactions_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    transaction = Transaction.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    # อัพเดทยอดเงินในบัญชี (เฉพาะกรณีสถานะเป็น 'completed')
    if transaction.status == 'completed':
        account = Account.query.get(transaction.account_id)
        if transaction.type == 'income':
            account.balance -= transaction.amount
        else:
            account.balance += transaction.amount

    # ลบไฟล์ใบเสร็จ (ถ้ามี)
    if transaction.receipt_path:
        delete_receipt(transaction.receipt_path)

    # ลบธุรกรรม
    db.session.delete(transaction)
    db.session.commit()

    flash('ลบธุรกรรมสำเร็จ!', 'success')
    return redirect(url_for('transactions.index'))


@transactions_bp.route('/view/<int:id>')
@login_required
def view(id):
    transaction = Transaction.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    return render_template('transactions/view.html', transaction=transaction, title='รายละเอียดธุรกรรม')