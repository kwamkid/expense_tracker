from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import db, BankAccount, Transaction, UserCompany
from app.forms import BankAccountForm
from app.services.balance_service import BalanceService

bank_accounts_bp = Blueprint('bank_accounts', __name__, url_prefix='/bank_accounts')


@bank_accounts_bp.route('/')
@login_required
def index():
    # ดึงบริษัทที่ active
    user_company = UserCompany.query.filter_by(user_id=current_user.id, active_company=True).first()

    if not user_company:
        flash('ไม่พบข้อมูลบริษัทที่ใช้งานอยู่ กรุณาเลือกบริษัท', 'warning')
        return redirect(url_for('auth.select_company'))

    company_id = user_company.company_id

    # แก้ไขการดึงบัญชีธนาคารให้ดึงเฉพาะในบริษัทปัจจุบัน
    bank_accounts = BankAccount.query.filter_by(user_id=current_user.id, company_id=company_id).all()
    return render_template('bank_accounts/index.html', bank_accounts=bank_accounts)


@bank_accounts_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    # ดึงบริษัทที่ active
    user_company = UserCompany.query.filter_by(user_id=current_user.id, active_company=True).first()

    if not user_company:
        flash('ไม่พบข้อมูลบริษัทที่ใช้งานอยู่ กรุณาเลือกบริษัท', 'warning')
        return redirect(url_for('auth.select_company'))

    company_id = user_company.company_id

    form = BankAccountForm()

    if form.validate_on_submit():
        bank_account = BankAccount(
            bank_name=form.bank_name.data,
            account_number=form.account_number.data,
            account_name=form.account_name.data,
            initial_balance=form.initial_balance.data or 0,  # ใช้ 0 ถ้าไม่ได้กรอก
            current_balance=form.initial_balance.data or 0,  # เริ่มต้นเท่ากับ initial_balance
            is_active=form.is_active.data,
            user_id=current_user.id,
            company_id=company_id  # เพิ่มการใส่ company_id ตรงนี้
        )
        db.session.add(bank_account)
        db.session.commit()

        flash('เพิ่มบัญชีธนาคารเรียบร้อยแล้ว', 'success')
        return redirect(url_for('bank_accounts.index'))

    return render_template('bank_accounts/form.html', form=form, title='เพิ่มบัญชีธนาคาร')


@bank_accounts_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    # ดึงบริษัทที่ active
    user_company = UserCompany.query.filter_by(user_id=current_user.id, active_company=True).first()

    if not user_company:
        flash('ไม่พบข้อมูลบริษัทที่ใช้งานอยู่ กรุณาเลือกบริษัท', 'warning')
        return redirect(url_for('auth.select_company'))

    company_id = user_company.company_id

    bank_account = BankAccount.query.get_or_404(id)

    # ตรวจสอบทั้ง user_id และ company_id
    if bank_account.user_id != current_user.id or bank_account.company_id != company_id:
        flash('คุณไม่มีสิทธิ์แก้ไขบัญชีนี้', 'error')
        return redirect(url_for('bank_accounts.index'))

    form = BankAccountForm(obj=bank_account)

    if form.validate_on_submit():
        # จัดการกับ initial_balance ที่อาจเป็น None
        new_initial_balance = form.initial_balance.data if form.initial_balance.data is not None else 0
        old_initial_balance = bank_account.initial_balance if bank_account.initial_balance is not None else 0

        bank_account.bank_name = form.bank_name.data
        bank_account.account_number = form.account_number.data
        bank_account.account_name = form.account_name.data
        bank_account.is_active = form.is_active.data

        # ถ้าเปลี่ยน initial_balance ต้องคำนวณ current_balance ใหม่
        if old_initial_balance != new_initial_balance:
            # คำนวณความแตกต่าง
            diff = new_initial_balance - old_initial_balance
            bank_account.initial_balance = new_initial_balance
            # ปรับ current_balance ตามความแตกต่าง
            if bank_account.current_balance is not None:
                bank_account.current_balance += diff
            else:
                bank_account.current_balance = new_initial_balance

        db.session.commit()

        # คำนวณยอดเงินใหม่
        BalanceService.update_bank_balance(bank_account.id)

        flash('แก้ไขบัญชีธนาคารเรียบร้อยแล้ว', 'success')
        return redirect(url_for('bank_accounts.index'))

    # Set default value for form fields
    if not form.is_submitted():
        form.initial_balance.data = bank_account.initial_balance or 0

    return render_template('bank_accounts/form.html', form=form, title='แก้ไขบัญชีธนาคาร', bank_account=bank_account)


@bank_accounts_bp.route('/delete/<int:id>')
@login_required
def delete(id):
    # ดึงบริษัทที่ active
    user_company = UserCompany.query.filter_by(user_id=current_user.id, active_company=True).first()

    if not user_company:
        flash('ไม่พบข้อมูลบริษัทที่ใช้งานอยู่ กรุณาเลือกบริษัท', 'warning')
        return redirect(url_for('auth.select_company'))

    company_id = user_company.company_id

    bank_account = BankAccount.query.get_or_404(id)

    # ตรวจสอบทั้ง user_id และ company_id
    if bank_account.user_id != current_user.id or bank_account.company_id != company_id:
        flash('คุณไม่มีสิทธิ์ลบบัญชีนี้', 'error')
        return redirect(url_for('bank_accounts.index'))

    # ตรวจสอบว่ามี transaction ที่ใช้บัญชีนี้หรือไม่
    transaction_count = Transaction.query.filter_by(bank_account_id=id).count()
    if transaction_count > 0:
        flash(f'ไม่สามารถลบบัญชีนี้ได้ เนื่องจากมีธุรกรรม {transaction_count} รายการที่ใช้บัญชีนี้', 'error')
        return redirect(url_for('bank_accounts.index'))

    db.session.delete(bank_account)
    db.session.commit()
    flash('ลบบัญชีธนาคารเรียบร้อยแล้ว', 'success')

    return redirect(url_for('bank_accounts.index'))


@bank_accounts_bp.route('/recalculate/<int:id>')
@login_required
def recalculate(id):
    """คำนวณยอดคงเหลือใหม่สำหรับบัญชีที่เลือก"""
    # ดึงบริษัทที่ active
    user_company = UserCompany.query.filter_by(user_id=current_user.id, active_company=True).first()

    if not user_company:
        flash('ไม่พบข้อมูลบริษัทที่ใช้งานอยู่ กรุณาเลือกบริษัท', 'warning')
        return redirect(url_for('auth.select_company'))

    company_id = user_company.company_id

    bank_account = BankAccount.query.get_or_404(id)

    # ตรวจสอบทั้ง user_id และ company_id
    if bank_account.user_id != current_user.id or bank_account.company_id != company_id:
        flash('คุณไม่มีสิทธิ์ดำเนินการนี้', 'error')
        return redirect(url_for('bank_accounts.index'))

    BalanceService.update_bank_balance(id)
    flash('คำนวณยอดคงเหลือใหม่เรียบร้อยแล้ว', 'success')

    return redirect(url_for('bank_accounts.index'))