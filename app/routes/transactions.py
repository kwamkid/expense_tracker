from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import db, Transaction, Category, BankAccount
from app.forms import TransactionForm
from app.services.balance_service import BalanceService
from datetime import datetime
import pytz

transactions_bp = Blueprint('transactions', __name__, url_prefix='/transactions')
bangkok_tz = pytz.timezone('Asia/Bangkok')


@transactions_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 20

    query = Transaction.query.filter_by(user_id=current_user.id)

    # Apply filters
    transaction_type = request.args.get('type')
    category_id = request.args.get('category')
    status = request.args.get('status')
    bank_account_id = request.args.get('bank_account')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if transaction_type:
        query = query.filter_by(type=transaction_type)
    if category_id:
        query = query.filter_by(category_id=category_id)
    if status:
        query = query.filter_by(status=status)
    if bank_account_id:
        query = query.filter_by(bank_account_id=bank_account_id)
    if start_date:
        query = query.filter(Transaction.transaction_date >= start_date)
    if end_date:
        query = query.filter(Transaction.transaction_date <= end_date)

    transactions = query.order_by(Transaction.transaction_date.desc(), Transaction.created_at.desc()) \
        .paginate(page=page, per_page=per_page)

    categories = Category.query.filter_by(user_id=current_user.id).all()
    bank_accounts = BankAccount.query.filter_by(user_id=current_user.id).all()

    return render_template('transactions/index.html',
                           transactions=transactions,
                           categories=categories,
                           bank_accounts=bank_accounts)


@transactions_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    form = TransactionForm()
    form.category_id.choices = [(c.id, c.name) for c in Category.query.filter_by(user_id=current_user.id).all()]
    form.bank_account_id.choices = [(0, 'เลือกบัญชี')] + [(b.id, f"{b.bank_name} - {b.account_number}")
                                                          for b in
                                                          BankAccount.query.filter_by(user_id=current_user.id).all()]

    if form.validate_on_submit():
        transaction = Transaction(
            amount=form.amount.data,
            description=form.description.data,
            transaction_date=form.transaction_date.data,
            transaction_time=form.transaction_time.data,
            type=form.type.data,
            category_id=form.category_id.data,
            bank_account_id=form.bank_account_id.data if form.bank_account_id.data != 0 else None,
            status=form.status.data,
            user_id=current_user.id
        )

        # ถ้าสถานะเป็น completed ให้บันทึก completed_date
        if form.status.data == 'completed':
            transaction.completed_date = datetime.now(bangkok_tz)

        db.session.add(transaction)
        db.session.commit()

        # อัพเดทยอดเงินถ้าสถานะเป็น completed และมีบัญชีธนาคาร
        if transaction.status == 'completed' and transaction.bank_account_id:
            BalanceService.update_bank_balance(transaction.bank_account_id)

        flash(f'เพิ่ม{form.type.data == "income" and "รายรับ" or "รายจ่าย"}เรียบร้อยแล้ว', 'success')
        return redirect(url_for('transactions.index'))

    return render_template('transactions/form.html', form=form, title='เพิ่มธุรกรรม')


@transactions_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    transaction = Transaction.query.get_or_404(id)

    if transaction.user_id != current_user.id:
        flash('คุณไม่มีสิทธิ์แก้ไขรายการนี้', 'error')
        return redirect(url_for('transactions.index'))

    form = TransactionForm(obj=transaction)
    form.category_id.choices = [(c.id, c.name) for c in Category.query.filter_by(user_id=current_user.id).all()]
    form.bank_account_id.choices = [(0, 'เลือกบัญชี')] + [(b.id, f"{b.bank_name} - {b.account_number}")
                                                          for b in
                                                          BankAccount.query.filter_by(user_id=current_user.id).all()]

    if form.validate_on_submit():
        old_status = transaction.status
        old_bank_account_id = transaction.bank_account_id

        transaction.amount = form.amount.data
        transaction.description = form.description.data
        transaction.transaction_date = form.transaction_date.data
        transaction.transaction_time = form.transaction_time.data
        transaction.type = form.type.data
        transaction.category_id = form.category_id.data
        transaction.bank_account_id = form.bank_account_id.data if form.bank_account_id.data != 0 else None
        transaction.status = form.status.data

        # อัพเดท completed_date ถ้าเปลี่ยนสถานะเป็น completed
        if form.status.data == 'completed' and old_status != 'completed':
            transaction.completed_date = datetime.now(bangkok_tz)
        elif form.status.data != 'completed':
            transaction.completed_date = None

        db.session.commit()

        # อัพเดทยอดเงินถ้าจำเป็น
        if old_bank_account_id != transaction.bank_account_id or old_status != transaction.status:
            if old_bank_account_id:
                BalanceService.update_bank_balance(old_bank_account_id)
            if transaction.bank_account_id:
                BalanceService.update_bank_balance(transaction.bank_account_id)

        flash('แก้ไขรายการเรียบร้อยแล้ว', 'success')
        return redirect(url_for('transactions.index'))

    # Set default value for select field
    if transaction.bank_account_id:
        form.bank_account_id.data = transaction.bank_account_id
    else:
        form.bank_account_id.data = 0

    return render_template('transactions/form.html', form=form, title='แก้ไขธุรกรรม')


@transactions_bp.route('/delete/<int:id>')
@login_required
def delete(id):
    transaction = Transaction.query.get_or_404(id)

    if transaction.user_id != current_user.id:
        flash('คุณไม่มีสิทธิ์ลบรายการนี้', 'error')
        return redirect(url_for('transactions.index'))

    bank_account_id = transaction.bank_account_id

    db.session.delete(transaction)
    db.session.commit()

    # อัพเดทยอดเงินถ้าจำเป็น
    if bank_account_id and transaction.status == 'completed':
        BalanceService.update_bank_balance(bank_account_id)

    flash('ลบรายการเรียบร้อยแล้ว', 'success')
    return redirect(url_for('transactions.index'))


@transactions_bp.route('/update_status/<int:id>', methods=['POST'])
@login_required
def update_status(id):
    """อัพเดทสถานะ transaction แบบ AJAX"""
    transaction = Transaction.query.get_or_404(id)

    if transaction.user_id != current_user.id:
        return jsonify({'success': False, 'message': 'ไม่มีสิทธิ์'}), 403

    data = request.get_json()
    new_status = data.get('status')

    if new_status not in ['pending', 'completed', 'cancelled']:
        return jsonify({'success': False, 'message': 'สถานะไม่ถูกต้อง'}), 400

    success = BalanceService.update_transaction_status(transaction.id, new_status)

    if success:
        return jsonify({'success': True, 'message': 'อัพเดทสถานะเรียบร้อย'})
    else:
        return jsonify({'success': False, 'message': 'เกิดข้อผิดพลาด'}), 500