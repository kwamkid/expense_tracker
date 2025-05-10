from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import db, Transaction, Category, BankAccount, UserCompany
from app.forms import TransactionForm
from app.services.balance_service import BalanceService
from app.routes.auth import create_default_categories
from datetime import datetime
import pytz

transactions_bp = Blueprint('transactions', __name__, url_prefix='/transactions')
bangkok_tz = pytz.timezone('Asia/Bangkok')


# app/routes/transactions.py - index
@transactions_bp.route('/')
@login_required
def index():
    # ตรวจสอบและดึงบริษัทที่ active
    user_company = UserCompany.query.filter_by(user_id=current_user.id, active_company=True).first()

    if not user_company:
        flash('ไม่พบข้อมูลบริษัทที่ใช้งานอยู่ กรุณาเลือกบริษัท', 'warning')
        return redirect(url_for('auth.select_company'))

    company_id = user_company.company_id

    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    # Validate per_page
    if per_page not in [20, 50, 100, 200]:
        per_page = 20

    # สร้าง query จาก company_id แทนที่จะใช้ user_id
    query = Transaction.query.filter_by(company_id=company_id)

    # Apply filters
    transaction_type = request.args.get('type')
    category_id = request.args.get('category')
    status = request.args.get('status')
    bank_account_id = request.args.get('bank_account')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    search = request.args.get('search')

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
    if search:
        query = query.filter(Transaction.description.ilike(f'%{search}%'))

    transactions = query.order_by(Transaction.transaction_date.desc(), Transaction.created_at.desc()) \
        .paginate(page=page, per_page=per_page)

    # ดึงข้อมูลหมวดหมู่และบัญชีธนาคารจาก company_id เดียวกัน
    categories = Category.query.filter_by(company_id=company_id).all()

    # ตรวจสอบว่ามีหมวดหมู่หรือไม่
    if len(categories) == 0:
        # ถ้าไม่มีหมวดหมู่ ให้ดึงข้อมูลจาก user_id แล้วย้ายไปยัง company_id
        orphan_categories = Category.query.filter_by(user_id=current_user.id).all()
        if orphan_categories:
            # ย้ายหมวดหมู่ให้เชื่อมโยงกับบริษัทปัจจุบัน
            for category in orphan_categories:
                category.company_id = company_id
            db.session.commit()
            flash('พบหมวดหมู่ที่ยังไม่มีการเชื่อมโยงกับบริษัท ระบบได้ทำการย้ายข้อมูลให้อัตโนมัติแล้ว', 'success')
            categories = Category.query.filter_by(company_id=company_id).all()
        else:
            # ถ้าไม่มีหมวดหมู่เลย ให้สร้างหมวดหมู่เริ่มต้น
            create_default_categories(current_user.id, company_id)
            flash('ระบบได้สร้างหมวดหมู่เริ่มต้นให้แล้ว', 'success')
            categories = Category.query.filter_by(company_id=company_id).all()

    bank_accounts = BankAccount.query.filter_by(company_id=company_id).all()

    return render_template('transactions/index.html',
                           transactions=transactions,
                           categories=categories,
                           bank_accounts=bank_accounts)


@transactions_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    # ตรวจสอบและดึงบริษัทที่ active
    user_company = UserCompany.query.filter_by(user_id=current_user.id, active_company=True).first()

    if not user_company:
        flash('ไม่พบข้อมูลบริษัทที่ใช้งานอยู่ กรุณาเลือกบริษัท', 'warning')
        return redirect(url_for('auth.select_company'))

    company_id = user_company.company_id

    # ตรวจสอบว่ามีหมวดหมู่ในบริษัทนี้หรือไม่
    categories = Category.query.filter_by(company_id=company_id).all()
    if len(categories) == 0:
        # ถ้าไม่มีหมวดหมู่ ให้ดึงข้อมูลจาก user_id แล้วย้ายไปยัง company_id
        orphan_categories = Category.query.filter_by(user_id=current_user.id).all()
        if orphan_categories:
            # ย้ายหมวดหมู่ให้เชื่อมโยงกับบริษัทปัจจุบัน
            for category in orphan_categories:
                category.company_id = company_id
            db.session.commit()
            flash('พบหมวดหมู่ที่ยังไม่มีการเชื่อมโยงกับบริษัท ระบบได้ทำการย้ายข้อมูลให้อัตโนมัติแล้ว', 'success')
            categories = Category.query.filter_by(company_id=company_id).all()
        else:
            # ถ้าไม่มีหมวดหมู่เลย ให้สร้างหมวดหมู่เริ่มต้น
            create_default_categories(current_user.id, company_id)
            flash('ระบบได้สร้างหมวดหมู่เริ่มต้นให้แล้ว', 'success')
            categories = Category.query.filter_by(company_id=company_id).all()

    form = TransactionForm()

    # แก้ไขเพื่อใช้ company_id ในการดึงข้อมูลหมวดหมู่
    form.category_id.choices = [(c.id, c.name) for c in categories]

    # แก้ไขเพื่อใช้ company_id ในการดึงข้อมูลบัญชีธนาคาร
    form.bank_account_id.choices = [(0, 'เลือกบัญชี')] + [(b.id, f"{b.bank_name} - {b.account_number}")
                                                          for b in
                                                          BankAccount.query.filter_by(
                                                              company_id=company_id).all()]

    if form.validate_on_submit():
        # ตรวจสอบว่าถ้าสถานะเป็น 'completed' จะต้องมีการเลือกบัญชีธนาคาร
        if form.status.data == 'completed' and (form.bank_account_id.data == 0 or form.bank_account_id.data is None):
            flash('กรุณาเลือกบัญชีธนาคารสำหรับรายการที่สำเร็จแล้ว', 'error')
            return render_template('transactions/form.html', form=form, title='เพิ่มธุรกรรม')

        transaction = Transaction(
            amount=form.amount.data,
            description=form.description.data,
            transaction_date=form.transaction_date.data,
            transaction_time=form.transaction_time.data,
            type=form.type.data,
            category_id=form.category_id.data,
            bank_account_id=form.bank_account_id.data if form.bank_account_id.data != 0 else None,
            status=form.status.data,
            user_id=current_user.id,
            company_id=company_id  # เพิ่มบรรทัดนี้เพื่อกำหนด company_id
        )

        # ถ้าสถานะเป็น completed ให้บันทึก completed_date
        if form.status.data == 'completed':
            transaction.completed_date = datetime.now(bangkok_tz)

        db.session.add(transaction)
        db.session.commit()

        # อัพเดทยอดเงินถ้าสถานะเป็น completed และมีบัญชีธนาคาร
        if transaction.status == 'completed' and transaction.bank_account_id:
            try:
                BalanceService.update_bank_balance(transaction.bank_account_id)
            except Exception as e:
                print(f"Error updating bank balance: {e}")
                flash('เพิ่มธุรกรรมสำเร็จแต่มีปัญหาในการอัพเดทยอดเงิน', 'warning')

        flash(f'เพิ่ม{form.type.data == "income" and "รายรับ" or "รายจ่าย"}เรียบร้อยแล้ว', 'success')
        return redirect(url_for('transactions.index'))

    return render_template('transactions/form.html', form=form, title='เพิ่มธุรกรรม')


@transactions_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    # ตรวจสอบและดึงบริษัทที่ active
    user_company = UserCompany.query.filter_by(user_id=current_user.id, active_company=True).first()

    if not user_company:
        flash('ไม่พบข้อมูลบริษัทที่ใช้งานอยู่ กรุณาเลือกบริษัท', 'warning')
        return redirect(url_for('auth.select_company'))

    company_id = user_company.company_id

    transaction = Transaction.query.get_or_404(id)

    # ตรวจสอบทั้ง user_id และ company_id
    if transaction.user_id != current_user.id or transaction.company_id != company_id:
        flash('คุณไม่มีสิทธิ์แก้ไขรายการนี้', 'error')
        return redirect(url_for('transactions.index'))

    form = TransactionForm(obj=transaction)

    # แก้ไขเพื่อใช้ company_id ในการดึงข้อมูลหมวดหมู่
    form.category_id.choices = [(c.id, c.name) for c in
                                Category.query.filter_by(company_id=company_id).all()]

    # แก้ไขเพื่อใช้ company_id ในการดึงข้อมูลบัญชีธนาคาร
    form.bank_account_id.choices = [(0, 'เลือกบัญชี')] + [(b.id, f"{b.bank_name} - {b.account_number}")
                                                          for b in
                                                          BankAccount.query.filter_by(
                                                              company_id=company_id).all()]

    if form.validate_on_submit():
        # ตรวจสอบว่าถ้าสถานะเป็น 'completed' จะต้องมีการเลือกบัญชีธนาคาร
        if form.status.data == 'completed' and (form.bank_account_id.data == 0 or form.bank_account_id.data is None):
            flash('กรุณาเลือกบัญชีธนาคารสำหรับรายการที่สำเร็จแล้ว', 'error')
            return render_template('transactions/form.html', form=form, title='แก้ไขธุรกรรม')

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
        # company_id ไม่ต้องอัพเดทเพราะยังคงใช้ค่าเดิม

        # อัพเดท completed_date ถ้าเปลี่ยนสถานะเป็น completed
        if form.status.data == 'completed' and old_status != 'completed':
            transaction.completed_date = datetime.now(bangkok_tz)
        elif form.status.data != 'completed':
            transaction.completed_date = None

        db.session.commit()

        # อัพเดทยอดเงินถ้าจำเป็น
        if old_bank_account_id != transaction.bank_account_id or old_status != transaction.status:
            if old_bank_account_id:
                try:
                    BalanceService.update_bank_balance(old_bank_account_id)
                except Exception as e:
                    print(f"Error updating old bank balance: {e}")

            if transaction.bank_account_id:
                try:
                    BalanceService.update_bank_balance(transaction.bank_account_id)
                except Exception as e:
                    print(f"Error updating new bank balance: {e}")
                    flash('แก้ไขธุรกรรมสำเร็จแต่มีปัญหาในการอัพเดทยอดเงิน', 'warning')

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

    # ตรวจสอบและดึงบริษัทที่ active
    user_company = UserCompany.query.filter_by(user_id=current_user.id, active_company=True).first()

    if not user_company:
        flash('ไม่พบข้อมูลบริษัทที่ใช้งานอยู่ กรุณาเลือกบริษัท', 'warning')
        return redirect(url_for('auth.select_company'))

    company_id = user_company.company_id

    # ตรวจสอบทั้ง user_id และ company_id เพื่อความปลอดภัย
    if transaction.user_id != current_user.id or transaction.company_id != company_id:
        flash('คุณไม่มีสิทธิ์ลบรายการนี้', 'error')
        return redirect(url_for('transactions.index'))

    bank_account_id = transaction.bank_account_id

    db.session.delete(transaction)
    db.session.commit()

    # อัพเดทยอดเงินถ้าจำเป็น
    if bank_account_id and transaction.status == 'completed':
        try:
            BalanceService.update_bank_balance(bank_account_id)
        except Exception as e:
            print(f"Error updating bank balance after delete: {e}")
            flash('ลบธุรกรรมสำเร็จแต่มีปัญหาในการอัพเดทยอดเงิน', 'warning')

    flash('ลบรายการเรียบร้อยแล้ว', 'success')
    return redirect(url_for('transactions.index'))


@transactions_bp.route('/update_status/<int:id>', methods=['POST'])
@login_required
def update_status(id):
    """อัพเดทสถานะ transaction แบบ AJAX"""
    transaction = Transaction.query.get_or_404(id)

    # ตรวจสอบและดึงบริษัทที่ active
    user_company = UserCompany.query.filter_by(user_id=current_user.id, active_company=True).first()

    if not user_company:
        return jsonify({'success': False, 'message': 'ไม่พบข้อมูลบริษัทที่ใช้งานอยู่'}), 403

    company_id = user_company.company_id

    # ตรวจสอบทั้ง user_id และ company_id
    if transaction.user_id != current_user.id or transaction.company_id != company_id:
        return jsonify({'success': False, 'message': 'ไม่มีสิทธิ์'}), 403

    data = request.get_json()
    new_status = data.get('status')
    bank_account_id = data.get('bank_account_id')

    if new_status not in ['pending', 'completed', 'cancelled']:
        return jsonify({'success': False, 'message': 'สถานะไม่ถูกต้อง'}), 400

    # ตรวจสอบว่าถ้าสถานะเป็น 'completed' จะต้องมีการเลือกบัญชีธนาคาร
    if new_status == 'completed' and not bank_account_id and not transaction.bank_account_id:
        return jsonify({'success': False, 'message': 'กรุณาเลือกบัญชีธนาคารสำหรับรายการที่สำเร็จแล้ว', 'needBankAccount': True}), 400

    # ถ้ามีการส่ง bank_account_id มา ให้อัพเดทด้วย
    if bank_account_id:
        bank_account = BankAccount.query.get(bank_account_id)
        if bank_account and bank_account.company_id == company_id:  # ตรวจสอบ company_id แทน user_id
            transaction.bank_account_id = bank_account_id
        else:
            return jsonify({'success': False, 'message': 'บัญชีธนาคารไม่ถูกต้อง'}), 400

    try:
        success = BalanceService.update_transaction_status(transaction.id, new_status)

        if success:
            db.session.commit()
            return jsonify({'success': True, 'message': 'อัพเดทสถานะเรียบร้อย'})
        else:
            return jsonify({'success': False, 'message': 'เกิดข้อผิดพลาด'}), 500
    except Exception as e:
        db.session.rollback()
        print(f"Error updating transaction status: {e}")
        return jsonify({'success': False, 'message': f'เกิดข้อผิดพลาด: {str(e)}'}), 500


# ตัวอย่างส่วนของโค้ดที่ต้องแก้ไขใน app/routes/transactions.py

@transactions_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    # ตรวจสอบและดึงบริษัทที่ active
    user_company = UserCompany.query.filter_by(user_id=current_user.id, active_company=True).first()

    if not user_company:
        flash('ไม่พบข้อมูลบริษัทที่ใช้งานอยู่ กรุณาเลือกบริษัท', 'warning')
        return redirect(url_for('auth.select_company'))

    company_id = user_company.company_id

    # ตรวจสอบว่ามีหมวดหมู่ในบริษัทนี้หรือไม่
    categories = Category.query.filter_by(company_id=company_id).all()
    if len(categories) == 0:
        # ถ้าไม่มีหมวดหมู่ ให้ดึงข้อมูลจาก user_id แล้วย้ายไปยัง company_id
        orphan_categories = Category.query.filter_by(user_id=current_user.id).all()
        if orphan_categories:
            # ย้ายหมวดหมู่ให้เชื่อมโยงกับบริษัทปัจจุบัน
            for category in orphan_categories:
                category.company_id = company_id
            db.session.commit()
            flash('พบหมวดหมู่ที่ยังไม่มีการเชื่อมโยงกับบริษัท ระบบได้ทำการย้ายข้อมูลให้อัตโนมัติแล้ว', 'success')
            categories = Category.query.filter_by(company_id=company_id).all()
        else:
            # ถ้าไม่มีหมวดหมู่เลย ให้สร้างหมวดหมู่เริ่มต้น
            create_default_categories(current_user.id, company_id)
            flash('ระบบได้สร้างหมวดหมู่เริ่มต้นให้แล้ว', 'success')
            categories = Category.query.filter_by(company_id=company_id).all()

    form = TransactionForm()

    # แก้ไขเพื่อใช้ company_id ในการดึงข้อมูลหมวดหมู่
    form.category_id.choices = [(c.id, c.name) for c in categories]

    # แก้ไขเพื่อใช้ company_id ในการดึงข้อมูลบัญชีธนาคาร (ไม่ใช้ user_id)
    form.bank_account_id.choices = [(0, 'เลือกบัญชี')] + [(b.id, f"{b.bank_name} - {b.account_number}")
                                                        for b in
                                                        BankAccount.query.filter_by(
                                                            company_id=company_id).all()]

    if form.validate_on_submit():
        # ตรวจสอบว่าถ้าสถานะเป็น 'completed' จะต้องมีการเลือกบัญชีธนาคาร
        if form.status.data == 'completed' and (form.bank_account_id.data == 0 or form.bank_account_id.data is None):
            flash('กรุณาเลือกบัญชีธนาคารสำหรับรายการที่สำเร็จแล้ว', 'error')
            return render_template('transactions/form.html', form=form, title='เพิ่มธุรกรรม')

        transaction = Transaction(
            amount=form.amount.data,
            description=form.description.data,
            transaction_date=form.transaction_date.data,
            transaction_time=form.transaction_time.data,
            type=form.type.data,
            category_id=form.category_id.data,
            bank_account_id=form.bank_account_id.data if form.bank_account_id.data != 0 else None,
            status=form.status.data,
            user_id=current_user.id,
            company_id=company_id  # เพิ่มบรรทัดนี้เพื่อกำหนด company_id
        )

        # ถ้าสถานะเป็น completed ให้บันทึก completed_date
        if form.status.data == 'completed':
            transaction.completed_date = datetime.now(bangkok_tz)

        db.session.add(transaction)
        db.session.commit()

        # อัพเดทยอดเงินถ้าสถานะเป็น completed และมีบัญชีธนาคาร
        if transaction.status == 'completed' and transaction.bank_account_id:
            try:
                BalanceService.update_bank_balance(transaction.bank_account_id)
            except Exception as e:
                print(f"Error updating bank balance: {e}")
                flash('เพิ่มธุรกรรมสำเร็จแต่มีปัญหาในการอัพเดทยอดเงิน', 'warning')

        flash(f'เพิ่ม{form.type.data == "income" and "รายรับ" or "รายจ่าย"}เรียบร้อยแล้ว', 'success')
        return redirect(url_for('transactions.index'))

    return render_template('transactions/form.html', form=form, title='เพิ่มธุรกรรม')


@transactions_bp.route('/api/categories')
@login_required
def get_categories():
    transaction_type = request.args.get('type', 'expense')

    # ตรวจสอบและดึงบริษัทที่ active
    user_company = UserCompany.query.filter_by(user_id=current_user.id, active_company=True).first()

    if not user_company:
        return jsonify([])

    company_id = user_company.company_id

    # แก้ไขเพื่อใช้ company_id ในการดึงข้อมูลหมวดหมู่
    categories = Category.query.filter_by(
        company_id=company_id,
        type=transaction_type
    ).all()

    # ถ้าไม่มีหมวดหมู่ ให้ตรวจสอบว่ามีข้อมูลใน user_id หรือไม่
    if len(categories) == 0:
        orphan_categories = Category.query.filter_by(
            user_id=current_user.id,
            type=transaction_type
        ).all()

        if orphan_categories:
            # ย้ายหมวดหมู่ให้เชื่อมโยงกับบริษัทปัจจุบัน
            for category in orphan_categories:
                category.company_id = company_id
            db.session.commit()

            # โหลดหมวดหมู่ใหม่
            categories = Category.query.filter_by(
                company_id=company_id,
                type=transaction_type
            ).all()

    return jsonify([{
        'id': cat.id,
        'name': cat.name,
        'keywords': cat.keywords
    } for cat in categories])