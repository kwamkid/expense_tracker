# app/views/auth.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from flask_login import login_user, logout_user, login_required, current_user
from app.forms.auth import LoginForm, RegistrationForm
from app.models.user import User
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

            # ถ้าผู้ใช้มีองค์กรที่ใช้งานอยู่แล้ว
            if user.active_organization_id:
                next_page = request.args.get('next')
                return redirect(next_page or url_for('dashboard.index'))

            # ถ้าผู้ใช้มีองค์กรแต่ยังไม่ได้เลือกองค์กรที่ใช้งาน
            if user.organizations:
                # กำหนดองค์กรแรกเป็นองค์กรที่ใช้งาน
                user.set_active_organization(user.organizations[0].id)
                return redirect(url_for('dashboard.index'))

            # ถ้าผู้ใช้ยังไม่มีองค์กร ให้ไปที่หน้าสร้างองค์กรใหม่
            flash('กรุณาสร้างองค์กรใหม่เพื่อเริ่มใช้งานระบบ', 'info')
            return redirect(url_for('organization.create'))
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
            password=form.password.data,
            first_name=form.first_name.data if hasattr(form, 'first_name') else None,
            last_name=form.last_name.data if hasattr(form, 'last_name') else None
        )
        db.session.add(user)
        db.session.commit()

        flash('สมัครสมาชิกสำเร็จ! กรุณาเข้าสู่ระบบ', 'success')
        return redirect(url_for('auth.login'))

    return render_template('auth/register.html', form=form, title='สมัครสมาชิก')


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()

    # ล้างข้อมูล session ที่เกี่ยวข้อง
    session.clear()

    flash('คุณได้ออกจากระบบแล้ว', 'info')
    return redirect(url_for('auth.login'))

