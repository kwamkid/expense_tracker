# app/views/organization.py
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, session
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models.organization import Organization
from app.models.user import User
from app.models.invitation import Invitation
from app.extensions import db
import os
from datetime import datetime, timedelta
import uuid

# ประกาศ Blueprint ก่อนที่จะใช้
organization_bp = Blueprint('organization', __name__, url_prefix='/organization')


@organization_bp.route('/')
@login_required
def index():
    """แสดงรายการองค์กรที่ผู้ใช้เป็นสมาชิก"""
    organizations = current_user.organizations
    return render_template(
        'organization/index.html',
        organizations=organizations,
        title='องค์กรของฉัน'
    )


@organization_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """สร้างองค์กรใหม่"""
    from app.forms.organization import OrganizationForm

    form = OrganizationForm()

    if form.validate_on_submit():
        # สร้างองค์กรใหม่
        organization = Organization(
            name=form.name.data,
            description=form.description.data,
            created_by=current_user.id
        )

        # อัปโหลดโลโก้ (ถ้ามี)
        if form.logo.data:
            logo_filename = save_organization_logo(form.logo.data)
            organization.logo_path = logo_filename

        # เพิ่มองค์กรลงในฐานข้อมูล
        db.session.add(organization)
        db.session.flush()  # ให้ได้ id ขององค์กร

        # เพิ่มผู้ใช้ปัจจุบันเป็นแอดมินขององค์กร
        from app.models.organization import organization_users
        db.session.execute(
            organization_users.insert().values(
                user_id=current_user.id,
                organization_id=organization.id,
                role='admin',
                joined_at=datetime.utcnow()
            )
        )

        # สร้างหมวดหมู่เริ่มต้นให้กับองค์กร
        from app.views.auth import create_default_categories
        create_default_categories(organization.id, current_user.id)

        # สร้างบัญชีเริ่มต้นให้กับองค์กร
        create_default_account(organization.id, current_user.id)

        db.session.commit()

        # ตั้งค่าองค์กรนี้เป็นองค์กรที่ใช้งานอยู่
        current_user.set_active_organization(organization.id)

        flash(f'สร้างองค์กร "{organization.name}" สำเร็จ!', 'success')
        return redirect(url_for('dashboard.index'))

    return render_template('organization/create.html', form=form, title='สร้างองค์กรใหม่')


@organization_bp.route('/select/<int:id>')
@login_required
def select(id):
    """เลือกองค์กรที่ต้องการใช้งาน"""
    # ตรวจสอบว่าผู้ใช้เป็นสมาชิกขององค์กรนี้หรือไม่
    organization = Organization.query.get_or_404(id)

    if organization not in current_user.organizations:
        flash('คุณไม่ได้เป็นสมาชิกขององค์กรนี้', 'danger')
        return redirect(url_for('organization.index'))

    # ตั้งค่าองค์กรที่เลือกเป็นองค์กรที่ใช้งานอยู่
    current_user.set_active_organization(id)

    flash(f'คุณกำลังใช้งานองค์กร "{organization.name}"', 'success')
    return redirect(url_for('dashboard.index'))


@organization_bp.route('/members/<int:id>')
@login_required
def members(id):
    """แสดงรายชื่อสมาชิกในองค์กร"""
    # ตรวจสอบว่าผู้ใช้เป็นสมาชิกขององค์กรนี้หรือไม่
    organization = Organization.query.get_or_404(id)

    if organization not in current_user.organizations:
        flash('คุณไม่ได้เป็นสมาชิกขององค์กรนี้', 'danger')
        return redirect(url_for('organization.index'))

    # ดึงรายชื่อสมาชิกพร้อมบทบาท
    from app.models.organization import organization_users
    from sqlalchemy import text

    member_roles = db.session.execute(
        text("""
        SELECT u.id, u.username, u.email, u.first_name, u.last_name, ou.role, ou.joined_at, u.line_id, u.line_profile_url
        FROM users u
        JOIN organization_users ou ON u.id = ou.user_id
        WHERE ou.organization_id = :org_id
        ORDER BY ou.joined_at
        """),
        {"org_id": id}
    ).fetchall()

    return render_template(
        'organization/members.html',
        organization=organization,
        member_roles=member_roles,
        current_user_role=organization.get_user_role(current_user.id),
        title=f'สมาชิก {organization.name}'
    )


@organization_bp.route('/update/<int:id>', methods=['GET', 'POST'])
@login_required
def update(id):
    """แก้ไขข้อมูลองค์กร"""
    from app.forms.organization import OrganizationForm

    # ตรวจสอบว่าผู้ใช้เป็นแอดมินขององค์กรนี้หรือไม่
    organization = Organization.query.get_or_404(id)

    if not organization.user_has_role(current_user.id, 'admin'):
        flash('คุณไม่มีสิทธิ์แก้ไขข้อมูลองค์กร', 'danger')
        return redirect(url_for('organization.index'))

    form = OrganizationForm(obj=organization)
    # กำหนดค่า id ให้ฟอร์ม เพื่อใช้ในการตรวจสอบชื่อซ้ำ
    form.id.data = organization.id

    if form.validate_on_submit():
        organization.name = form.name.data
        organization.description = form.description.data

        # อัปโหลดโลโก้ใหม่ (ถ้ามี)
        if form.logo.data:
            # ลบโลโก้เดิม (ถ้ามี)
            if organization.logo_path:
                delete_organization_logo(organization.logo_path)

            # บันทึกโลโก้ใหม่
            logo_filename = save_organization_logo(form.logo.data)
            organization.logo_path = logo_filename

        db.session.commit()

        flash('อัปเดตข้อมูลองค์กรเรียบร้อย', 'success')
        return redirect(url_for('organization.index'))

    return render_template(
        'organization/update.html',
        form=form,
        organization=organization,
        title=f'แก้ไขข้อมูลองค์กร {organization.name}'
    )


@organization_bp.route('/change-role/<int:org_id>/<int:user_id>', methods=['POST'])
@login_required
def change_role(org_id, user_id):
    """เปลี่ยนบทบาทของสมาชิกในองค์กร"""
    # ตรวจสอบว่าผู้ใช้เป็นแอดมินขององค์กรนี้หรือไม่
    organization = Organization.query.get_or_404(org_id)

    if not organization.user_has_role(current_user.id, 'admin'):
        flash('คุณไม่มีสิทธิ์เปลี่ยนบทบาทของสมาชิก', 'danger')
        return redirect(url_for('organization.members', id=org_id))

    # ไม่อนุญาตให้แก้ไขบทบาทของตัวเอง
    if user_id == current_user.id:
        flash('คุณไม่สามารถเปลี่ยนบทบาทของตัวเองได้', 'danger')
        return redirect(url_for('organization.members', id=org_id))

    role = request.form.get('role')
    if role not in ['admin', 'member', 'viewer']:
        flash('บทบาทไม่ถูกต้อง', 'danger')
        return redirect(url_for('organization.members', id=org_id))

    # อัปเดตบทบาทในฐานข้อมูล
    from app.models.organization import organization_users
    db.session.execute(
        organization_users.update()
        .where(
            (organization_users.c.user_id == user_id) &
            (organization_users.c.organization_id == org_id)
        )
        .values(role=role)
    )
    db.session.commit()

    user = User.query.get(user_id)
    flash(f'เปลี่ยนบทบาทของ {user.email} เป็น {role} แล้ว', 'success')

    return redirect(url_for('organization.members', id=org_id))


@organization_bp.route('/remove/<int:org_id>/<int:user_id>', methods=['POST'])
@login_required
def remove_member(org_id, user_id):
    """ลบสมาชิกออกจากองค์กร"""
    # ตรวจสอบว่าผู้ใช้เป็นแอดมินขององค์กรนี้หรือไม่
    organization = Organization.query.get_or_404(org_id)

    if not organization.user_has_role(current_user.id, 'admin'):
        flash('คุณไม่มีสิทธิ์ลบสมาชิก', 'danger')
        return redirect(url_for('organization.members', id=org_id))

    # ไม่อนุญาตให้ลบตัวเอง
    if user_id == current_user.id:
        flash('คุณไม่สามารถลบตัวเองออกจากองค์กรได้', 'danger')
        return redirect(url_for('organization.members', id=org_id))

    # ลบสมาชิกจากองค์กร
    from app.models.organization import organization_users
    db.session.execute(
        organization_users.delete()
        .where(
            (organization_users.c.user_id == user_id) &
            (organization_users.c.organization_id == org_id)
        )
    )
    db.session.commit()

    user = User.query.get(user_id)
    flash(f'ลบ {user.username} ออกจากองค์กรแล้ว', 'success')

    return redirect(url_for('organization.members', id=org_id))


@organization_bp.route('/generate_invite/<int:id>', methods=['POST'])
@login_required
def generate_invite(id):
    """สร้างลิงก์เชิญสำหรับองค์กร"""
    # ตรวจสอบว่าผู้ใช้เป็นแอดมินขององค์กรนี้หรือไม่
    organization = Organization.query.get_or_404(id)

    if not organization.user_has_role(current_user.id, 'admin'):
        flash('คุณไม่มีสิทธิ์สร้างลิงก์เชิญ', 'danger')
        return redirect(url_for('organization.members', id=id))

    # สร้าง invitation token
    role = request.form.get('role', 'member')
    from app.views.auth import generate_invitation_token
    token = generate_invitation_token(organization.id, role)

    # สร้าง invitation link
    invite_url = url_for('organization.join', token=token, _external=True)

    # สร้างหรืออัพเดตบันทึกการเชิญ
    invitation = Invitation(
        token=token,
        organization_id=organization.id,
        created_by=current_user.id,
        role=role,
        expires_at=datetime.utcnow() + timedelta(days=7)  # หมดอายุใน 7 วัน
    )
    db.session.add(invitation)
    db.session.commit()

    current_app.logger.info(f"Generated invitation link for organization {organization.id} with role {role}")

    return render_template(
        'organization/invite_link.html',
        invite_url=invite_url,
        organization=organization,
        role=role
    )


@organization_bp.route('/join/<token>')
def join(token):
    """เข้าร่วมองค์กรด้วยลิงก์เชิญ"""
    # ตรวจสอบ token
    invitation = Invitation.query.filter_by(token=token).first()

    if not invitation:
        flash('ลิงก์เชิญไม่ถูกต้อง', 'danger')
        return redirect(url_for('auth.login'))

    if invitation.is_expired():
        flash('ลิงก์เชิญหมดอายุแล้ว', 'danger')
        return redirect(url_for('auth.login'))

    if invitation.is_used():
        flash('ลิงก์เชิญนี้ถูกใช้ไปแล้ว', 'warning')
        return redirect(url_for('auth.login'))

    # บันทึก token ไว้ใน session เพื่อใช้หลังจาก login
    session['invitation_token'] = token

    if current_user.is_authenticated:
        # ถ้าผู้ใช้ login อยู่แล้ว ดำเนินการเพิ่มเข้าองค์กรทันที
        from app.views.auth import process_invitation
        return process_invitation(token, current_user)
    else:
        # ถ้ายังไม่ได้ login ให้เข้าสู่หน้า login ด้วย LINE
        flash('กรุณาเข้าสู่ระบบด้วย LINE เพื่อเข้าร่วมองค์กร', 'info')
        return redirect(url_for('auth.line_login'))


# Utility functions

def save_organization_logo(file):
    """บันทึกไฟล์โลโก้องค์กร"""
    if not file:
        return None

    # สร้างชื่อไฟล์ใหม่
    timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
    filename = secure_filename(file.filename)
    extension = filename.rsplit('.', 1)[1].lower() if '.' in filename else 'jpg'
    new_filename = f"logo_{timestamp}_{uuid.uuid4().hex[:8]}.{extension}"

    # กำหนดพาธสำหรับบันทึกไฟล์
    upload_folder = os.path.join(current_app.root_path, 'static/uploads/organizations')
    os.makedirs(upload_folder, exist_ok=True)
    file_path = os.path.join(upload_folder, new_filename)

    # บันทึกไฟล์
    file.save(file_path)

    return new_filename


def delete_organization_logo(filename):
    """ลบไฟล์โลโก้องค์กร"""
    if not filename:
        return False

    filepath = os.path.join(current_app.root_path, 'static/uploads/organizations', filename)
    if os.path.exists(filepath):
        os.remove(filepath)
        return True
    return False


def create_default_account(organization_id, user_id):
    """สร้างบัญชีเริ่มต้นสำหรับองค์กรใหม่"""
    from app.models.account import Account

    account = Account(
        name='บัญชีหลัก',
        balance=0.0,
        is_active=True,
        organization_id=organization_id,
        created_by=user_id,
        updated_by=user_id
    )
    db.session.add(account)