# app/views/auth.py
from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from app.forms.auth import LoginForm, RegistrationForm
from app.models import User
from app.extensions import db

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard.index'))
        else:
            flash('อีเมลหรือรหัสผ่านไม่ถูกต้อง', 'danger')

    return render_template('auth/login.html', form=form, title='เข้าสู่ระบบ')


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=form.password.data
        )
        db.session.add(user)
        db.session.commit()

        # สร้างหมวดหมู่เริ่มต้น
        create_default_categories(user.id)
        # สร้างบัญชีเริ่มต้น
        create_default_account(user.id)

        flash('สมัครสมาชิกสำเร็จ! กรุณาเข้าสู่ระบบ', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form, title='สมัครสมาชิก')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('คุณได้ออกจากระบบแล้ว', 'info')
    return redirect(url_for('auth.login'))


# app/views/auth.py - แก้ไขฟังก์ชัน create_default_categories

def create_default_categories(user_id):
    """สร้างหมวดหมู่เริ่มต้นสำหรับผู้ใช้ใหม่"""
    from app.models import Category

    # หมวดหมู่รายรับ
    income_categories = [
        {'name': 'ค่าคอร์ส', 'color': '#27ae60', 'icon': 'money-bill'},
        {'name': 'ค่าคอร์ส Summer', 'color': '#2ecc71', 'icon': 'sun'},
        {'name': 'ค่าคอร์สแข่ง', 'color': '#3498db', 'icon': 'trophy'},
        {'name': 'อื่นๆ', 'color': '#34495e', 'icon': 'plus-circle'}
    ]

    # หมวดหมู่รายจ่าย
    expense_categories = [
        {'name': 'อาหาร', 'color': '#e74c3c', 'icon': 'utensils'},
        {'name': 'ก่อสร้าง/ต่อเติม', 'color': '#d35400', 'icon': 'home'},
        {'name': 'ค่าอุปกรณ์การสอน', 'color': '#f39c12', 'icon': 'book'},
        {'name': 'ค่าเช่า/บิล/สาธารณูปโภค', 'color': '#f1c40f', 'icon': 'file-invoice'},
        {'name': 'การเดินทาง', 'color': '#1abc9c', 'icon': 'car'},
        {'name': 'อื่นๆ', 'color': '#7f8c8d', 'icon': 'tag'}
    ]

    # เพิ่มหมวดหมู่รายรับ
    for cat in income_categories:
        category = Category(
            name=cat['name'],
            type='income',
            color=cat['color'],
            icon=cat['icon'],
            user_id=user_id
        )
        db.session.add(category)

    # เพิ่มหมวดหมู่รายจ่าย
    for cat in expense_categories:
        category = Category(
            name=cat['name'],
            type='expense',
            color=cat['color'],
            icon=cat['icon'],
            user_id=user_id
        )
        db.session.add(category)

    db.session.commit()


def create_default_account(user_id):
    """สร้างบัญชีเริ่มต้นสำหรับผู้ใช้ใหม่"""
    from app.models import Account

    account = Account(
        name='บัญชีหลัก',
        balance=0.0,
        is_active=True,
        user_id=user_id
    )
    db.session.add(account)
    db.session.commit()