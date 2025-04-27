# app/views/auth.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, session, current_app, jsonify
from flask_login import login_user, logout_user, login_required, current_user
from app.forms.auth import LoginForm, RegistrationForm
from app.models.user import User
from app.models.invitation import Invitation
from app.models.organization import Organization, organization_users
from app.extensions import db
import requests
import os
import secrets
import string
from datetime import datetime, timedelta
import uuid

# กำหนดค่า LINE API
LINE_CLIENT_ID = os.environ.get('LINE_CLIENT_ID', 'YOUR_LINE_CLIENT_ID')
LINE_CLIENT_SECRET = os.environ.get('LINE_CLIENT_SECRET', 'YOUR_LINE_CLIENT_SECRET')

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """หน้าเข้าสู่ระบบปกติ - แนะนำให้ใช้ LINE Login แทน"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard.index'))

    # ตรวจสอบว่ามี invitation token หรือไม่
    invitation_token = request.args.get('token')
    if invitation_token:
        session['invitation_token'] = invitation_token
        return redirect(url_for('auth.line_login'))

    return render_template('auth/login.html', title='เข้าสู่ระบบ')


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
        current_app.logger.info(f"LINE Login successful for user {user.id}")

        # ตรวจสอบว่ามี invitation ที่รอดำเนินการหรือไม่
        invitation_token = session.pop('invitation_token', None)
        if invitation_token:
            return process_invitation(invitation_token, user)

        # ถ้าผู้ใช้มีองค์กรที่ใช้งานอยู่แล้ว
        if user.active_organization_id:
            return redirect(url_for('dashboard.index'))

        # ถ้าผู้ใช้มีองค์กรแต่ยังไม่ได้เลือกองค์กรที่ใช้งาน
        if user.organizations:
            # กำหนดองค์กรแรกเป็นองค์กรที่ใช้งาน
            user.set_active_organization(user.organizations[0].id)
            return redirect(url_for('dashboard.index'))

        # ถ้าผู้ใช้ยังไม่มีองค์กร ให้ไปที่หน้าสร้างองค์กรใหม่
        flash('กรุณาสร้างองค์กรใหม่เพื่อเริ่มใช้งานระบบ', 'info')
        return redirect(url_for('organization.create'))
    else:
        # ถ้ายังไม่มีผู้ใช้นี้ ให้สร้างบัญชีใหม่
        # สร้าง random password สำหรับบัญชีใหม่
        random_password = generate_random_password()

        new_user = User(
            username=profile.get('displayName', f"LINE User {line_id[:8]}"),
            email=f"{line_id}@line.user",  # สร้าง email จาก line_id
            password=random_password,
            line_id=line_id,
            line_profile_url=profile.get('pictureUrl')
        )
        db.session.add(new_user)
        db.session.commit()

        current_app.logger.info(f"Created new user via LINE Login: {new_user.id}")
        login_user(new_user)
        flash('สร้างบัญชีผู้ใช้ใหม่ด้วย LINE สำเร็จ!', 'success')

        # ตรวจสอบว่ามี invitation ที่รอดำเนินการหรือไม่
        invitation_token = session.pop('invitation_token', None)
        if invitation_token:
            return process_invitation(invitation_token, new_user)

        # ถ้าไม่มี invitation ให้ไปที่หน้าสร้างองค์กรใหม่
        flash('กรุณาสร้างองค์กรใหม่เพื่อเริ่มใช้งานระบบ', 'info')
        return redirect(url_for('organization.create'))


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()

    # ล้างข้อมูล session ที่เกี่ยวข้อง
    session.clear()

    flash('คุณได้ออกจากระบบแล้ว', 'info')
    return redirect(url_for('auth.login'))


def process_invitation(token, user):
    """ดำเนินการตาม invitation หลังจาก login สำเร็จ"""
    invitation = Invitation.query.filter_by(token=token).first()

    if not invitation or invitation.is_expired():
        flash('ลิงก์เชิญไม่ถูกต้องหรือหมดอายุแล้ว', 'danger')
        return redirect(url_for('dashboard.index'))

    if invitation.is_used():
        flash('ลิงก์เชิญนี้ถูกใช้ไปแล้ว', 'warning')
        return redirect(url_for('dashboard.index'))

    organization = Organization.query.get(invitation.organization_id)

    # ตรวจสอบว่าผู้ใช้เป็นสมาชิกองค์กรนี้อยู่แล้วหรือไม่
    if organization in user.organizations:
        flash(f'คุณเป็นสมาชิกขององค์กร "{organization.name}" อยู่แล้ว', 'info')
    else:
        # เพิ่มผู้ใช้เข้าองค์กรด้วยบทบาทที่กำหนด
        db.session.execute(
            organization_users.insert().values(
                user_id=user.id,
                organization_id=organization.id,
                role=invitation.role,
                joined_at=datetime.utcnow()
            )
        )

        # ทำเครื่องหมายว่าลิงก์เชิญถูกใช้แล้ว
        invitation.mark_as_used(user.id)

        db.session.commit()
        flash(f'คุณได้เข้าร่วมองค์กร "{organization.name}" เรียบร้อยแล้ว', 'success')

    # ตั้งค่าองค์กรนี้เป็นองค์กรที่ใช้งานอยู่
    user.set_active_organization(organization.id)

    return redirect(url_for('dashboard.index'))


# Utility functions
def generate_random_token(length=32):
    """สร้าง token แบบสุ่ม"""
    return secrets.token_hex(length)


def generate_random_password(length=12):
    """สร้างรหัสผ่านแบบสุ่มที่มีความปลอดภัย"""
    alphabet = string.ascii_letters + string.digits + string.punctuation
    return ''.join(secrets.choice(alphabet) for _ in range(length))


def generate_invitation_token(organization_id, role):
    """สร้าง token สำหรับการเชิญ"""
    token = f"{organization_id}-{role}-{uuid.uuid4().hex}"
    return token


# สร้างหมวดหมู่เริ่มต้นสำหรับองค์กรใหม่
def create_default_categories(organization_id, user_id=None):
    """สร้างหมวดหมู่เริ่มต้นสำหรับองค์กรใหม่"""
    from app.models.category import Category

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
            organization_id=organization_id,
            created_by=user_id,
            updated_by=user_id
        )
        db.session.add(category)

    # เพิ่มหมวดหมู่รายจ่าย
    for cat in expense_categories:
        category = Category(
            name=cat['name'],
            type='expense',
            color=cat['color'],
            icon=cat['icon'],
            organization_id=organization_id,
            created_by=user_id,
            updated_by=user_id
        )
        db.session.add(category)