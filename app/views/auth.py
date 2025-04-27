# app/views/auth.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, session , jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app.forms.auth import LoginForm, RegistrationForm
from app.models.user import User
from app.extensions import db
import requests

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


@auth_bp.route('/line_login')
def line_login():
    """เริ่มการ login ด้วย LINE"""
    # สร้าง state token เพื่อป้องกัน CSRF
    state = generate_random_token()
    session['line_login_state'] = state

    # กำหนด URL สำหรับ LINE Login
    line_auth_url = "https://access.line.me/oauth2/v2.1/authorize"
    callback_url = url_for('auth.line_callback', _external=True)

    # สร้างลิงก์สำหรับเริ่มการ login
    auth_url = f"{line_auth_url}?response_type=code&client_id={LINE_CLIENT_ID}&redirect_uri={callback_url}&state={state}&scope=profile%20openid"

    return redirect(auth_url)


@auth_bp.route('/line_callback')
def line_callback():
    """รับข้อมูลหลังจาก LINE Login สำเร็จ"""
    # ตรวจสอบ state เพื่อป้องกัน CSRF
    if request.args.get('state') != session.pop('line_login_state', None):
        flash('ข้อผิดพลาดด้านความปลอดภัย กรุณาลองใหม่อีกครั้ง', 'danger')
        return redirect(url_for('auth.login'))

    # ดึง access token
    code = request.args.get('code')
    token_url = "https://api.line.me/oauth2/v2.1/token"
    callback_url = url_for('auth.line_callback', _external=True)

    token_data = {
        'grant_type': 'authorization_code',
        'code': code,
        'redirect_uri': callback_url,
        'client_id': LINE_CLIENT_ID,
        'client_secret': LINE_CLIENT_SECRET
    }

    token_response = requests.post(token_url, data=token_data)
    token_info = token_response.json()

    # ดึงข้อมูลผู้ใช้จาก LINE
    profile_url = "https://api.line.me/v2/profile"
    headers = {'Authorization': f"Bearer {token_info['access_token']}"}
    profile_response = requests.get(profile_url, headers=headers)
    profile = profile_response.json()

    # ตรวจสอบว่ามีผู้ใช้นี้ในระบบแล้วหรือไม่
    line_id = profile['userId']
    user = User.query.filter_by(line_id=line_id).first()

    if user:
        # ถ้ามีผู้ใช้นี้อยู่แล้ว ให้เข้าสู่ระบบ
        login_user(user)

        # ตรวจสอบว่ามี invitation ที่รอดำเนินการหรือไม่
        invitation_token = session.pop('invitation_token', None)
        if invitation_token:
            return process_invitation(invitation_token, user)

        return redirect(url_for('dashboard.index'))
    else:
        # ถ้ายังไม่มีผู้ใช้นี้ ให้สร้างบัญชีใหม่
        new_user = User(
            username=profile['displayName'],
            email=f"{line_id}@line.user",  # สร้าง email จาก line_id
            line_id=line_id,
            profile_image=profile['pictureUrl'],
            password=generate_random_password()  # สร้าง password สุ่ม
        )
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)
        flash('สร้างบัญชีผู้ใช้ใหม่ด้วย LINE สำเร็จ!', 'success')

        # ตรวจสอบว่ามี invitation ที่รอดำเนินการหรือไม่
        invitation_token = session.pop('invitation_token', None)
        if invitation_token:
            return process_invitation(invitation_token, new_user)

        return redirect(url_for('organization.create'))

