# app/views/accounts.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app.forms.account import AccountForm
from app.models import Account
from app.extensions import db

accounts_bp = Blueprint('accounts', __name__, url_prefix='/accounts')


@accounts_bp.route('/')
@login_required
def index():
    accounts = Account.query.filter_by(user_id=current_user.id).all()
    return render_template('accounts/index.html', accounts=accounts, title='บัญชีของฉัน')


@accounts_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = AccountForm()

    if form.validate_on_submit():
        account = Account(
            name=form.name.data,
            balance=form.balance.data,
            is_active=form.is_active.data,
            user_id=current_user.id
        )
        db.session.add(account)
        db.session.commit()

        flash('เพิ่มบัญชีสำเร็จ!', 'success')
        return redirect(url_for('accounts.index'))

    return render_template('accounts/create.html', form=form, title='เพิ่มบัญชีใหม่')


@accounts_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    account = Account.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    form = AccountForm(obj=account)

    if form.validate_on_submit():
        account.name = form.name.data
        account.balance = form.balance.data
        account.is_active = form.is_active.data

        db.session.commit()
        flash('แก้ไขบัญชีสำเร็จ!', 'success')
        return redirect(url_for('accounts.index'))

    return render_template('accounts/edit.html', form=form, account=account, title='แก้ไขบัญชี')


@accounts_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    account = Account.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    # ตรวจสอบว่ามีธุรกรรมในบัญชีหรือไม่
    if account.transactions.count() > 0:
        flash('ไม่สามารถลบบัญชีที่มีธุรกรรมได้ โปรดลบธุรกรรมก่อน', 'danger')
        return redirect(url_for('accounts.index'))

    db.session.delete(account)
    db.session.commit()

    flash('ลบบัญชีสำเร็จ!', 'success')
    return redirect(url_for('accounts.index'))