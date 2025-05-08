# app/routes/settings.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, jsonify
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models import db, Category, InviteToken, Transaction, ImportHistory, User, Company, BankAccount, UserCompany
from app.forms import CompanySettingsForm, CategoryForm
import os
import uuid
from datetime import date, datetime
import pytz
from app.routes.auth import create_default_categories, create_default_bank_account

bangkok_tz = pytz.timezone('Asia/Bangkok')
settings_bp = Blueprint('settings', __name__, url_prefix='/settings')


@settings_bp.route('/company', methods=['GET', 'POST'])
@login_required
def company():
    # ดึงบริษัทที่ active จาก UserCompany
    active_company = UserCompany.query.filter_by(
        user_id=current_user.id,
        active_company=True
    ).first()

    if not active_company:
        flash('ไม่พบข้อมูลบริษัทที่ใช้งานอยู่', 'error')
        return redirect(url_for('main.dashboard'))

    company = active_company.company

    # สร้าง form พร้อมข้อมูลบริษัท
    form = CompanySettingsForm(obj=company)

    if form.validate_on_submit():
        company.name = form.company_name.data
        company.address = form.company_address.data
        company.tax_id = form.tax_id.data

        # Handle logo upload
        if form.logo.data:
            file = form.logo.data
            if file and allowed_file(file.filename):
                # Delete old logo
                if company.logo_path:
                    old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'logo', company.logo_path)
                    if os.path.exists(old_path):
                        os.remove(old_path)

                # Save new logo
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], 'logo', unique_filename)
                file.save(filepath)
                company.logo_path = unique_filename

        db.session.commit()
        flash('บันทึกข้อมูลเรียบร้อยแล้ว', 'success')
        return redirect(url_for('settings.company'))

    return render_template('settings/company.html', form=form, company=company)


@settings_bp.route('/categories')
@login_required
def categories():
    # อาจต้องแก้ไขจาก user_id เป็น company_id
    active_company = UserCompany.query.filter_by(
        user_id=current_user.id,
        active_company=True
    ).first()

    if not active_company:
        flash('ไม่พบข้อมูลบริษัทที่ใช้งานอยู่', 'error')
        return redirect(url_for('main.dashboard'))

    categories = Category.query.filter_by(company_id=active_company.company_id).all()
    return render_template('settings/categories.html', categories=categories)


@settings_bp.route('/categories/add', methods=['GET', 'POST'])
@login_required
def add_category():
    form = CategoryForm()

    if form.validate_on_submit():
        # ดึงบริษัทที่ active
        active_company = UserCompany.query.filter_by(
            user_id=current_user.id,
            active_company=True
        ).first()

        if not active_company:
            flash('ไม่พบข้อมูลบริษัทที่ใช้งานอยู่', 'error')
            return redirect(url_for('main.dashboard'))

        category = Category(
            name=form.name.data,
            type=form.type.data,
            keywords=form.keywords.data,
            user_id=current_user.id,
            company_id=active_company.company_id
        )
        db.session.add(category)
        db.session.commit()

        flash('เพิ่มหมวดหมู่เรียบร้อยแล้ว', 'success')
        return redirect(url_for('settings.categories'))

    return render_template('settings/category_form.html', form=form, title='เพิ่มหมวดหมู่')


@settings_bp.route('/profile')
@login_required
def profile():
    return render_template('settings/profile.html')


@settings_bp.route('/create_invite', methods=['GET'])
@login_required
def create_invite():
    """สร้างคำเชิญใหม่และส่งคืน URL (ใช้กับ AJAX)"""
    # ดึงบริษัทที่ active
    active_company = UserCompany.query.filter_by(
        user_id=current_user.id,
        active_company=True
    ).first()

    if not active_company:
        return jsonify({'success': False, 'error': 'ไม่พบบริษัทที่ใช้งานอยู่'})

    # สร้าง token ใหม่
    token = str(uuid.uuid4())
    invite = InviteToken(
        token=token,
        created_by=current_user.id,
        company_id=active_company.company_id
    )
    db.session.add(invite)
    db.session.commit()

    # สร้าง URL สำหรับเชิญ
    invite_url = url_for('auth.login', invite=token, _external=True)

    # ส่งคืนเป็น JSON
    return jsonify({
        'success': True,
        'invite_url': invite_url,
        'token': token
    })


@settings_bp.route('/cancel_invite/<int:id>')
@login_required
def cancel_invite(id):
    """ยกเลิกคำเชิญที่ยังไม่ได้ใช้"""
    # ดึงบริษัทที่ active
    active_company = UserCompany.query.filter_by(
        user_id=current_user.id,
        active_company=True
    ).first()

    if not active_company:
        flash('ไม่พบข้อมูลบริษัทที่ใช้งานอยู่', 'error')
        return redirect(url_for('main.dashboard'))

    # ตรวจสอบว่าคำเชิญอยู่ในบริษัทของผู้ใช้หรือไม่
    invite = InviteToken.query.filter_by(
        id=id,
        company_id=active_company.company_id,
        used=False
    ).first_or_404()

    # ลบคำเชิญ
    db.session.delete(invite)
    db.session.commit()

    flash('ยกเลิกคำเชิญเรียบร้อยแล้ว', 'success')
    return redirect(url_for('settings.company_members'))


@settings_bp.route('/invite')
@login_required
def invite():
    # ดึงบริษัทที่ active
    active_company = UserCompany.query.filter_by(
        user_id=current_user.id,
        active_company=True
    ).first()

    if not active_company:
        flash('ไม่พบข้อมูลบริษัทที่ใช้งานอยู่', 'error')
        return redirect(url_for('main.dashboard'))

    # Generate invite link
    token = str(uuid.uuid4())
    invite = InviteToken(
        token=token,
        created_by=current_user.id,
        company_id=active_company.company_id
    )
    db.session.add(invite)
    db.session.commit()

    invite_url = url_for('auth.login', invite=token, _external=True)
    return render_template('settings/invite.html', invite_url=invite_url)


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg'}


# ในไฟล์ app/routes/settings.py
# แก้ไขฟังก์ชัน clear_data

@settings_bp.route('/clear-data', methods=['GET', 'POST'])
@login_required
def clear_data():
    # ดึงบริษัทที่ active
    active_company = UserCompany.query.filter_by(
        user_id=current_user.id,
        active_company=True
    ).first()

    if not active_company:
        flash('ไม่พบข้อมูลบริษัทที่ใช้งานอยู่', 'error')
        return redirect(url_for('main.dashboard'))

    company_id = active_company.company_id

    if request.method == 'POST':
        # ตรวจสอบการยืนยัน
        confirm_text = request.form.get('confirm_text', '')
        if confirm_text.lower() == 'ลบข้อมูลทั้งหมด':
            try:
                # ลบ transactions ทั้งหมดของบริษัท
                transactions = Transaction.query.filter_by(company_id=company_id).all()
                for transaction in transactions:
                    db.session.delete(transaction)

                # ลบ import history ทั้งหมดของบริษัท
                import_histories = ImportHistory.query.filter_by(company_id=company_id).all()
                for history in import_histories:
                    db.session.delete(history)

                # ลบหมวดหมู่เก่าทั้งหมด
                categories = Category.query.filter_by(company_id=company_id).all()
                for category in categories:
                    db.session.delete(category)

                # ลบบัญชีธนาคารทั้งหมด
                bank_accounts = BankAccount.query.filter_by(company_id=company_id).all()
                for account in bank_accounts:
                    db.session.delete(account)

                # อัปเดตข้อมูลบริษัท
                company = Company.query.get(company_id)
                company.name = "Amp Tech Co.,Ltd"

                db.session.commit()

                # สร้างหมวดหมู่ค่าเริ่มต้นใหม่
                create_default_categories(current_user.id, company_id)

                # สร้างบัญชีธนาคารเริ่มต้นใหม่
                create_default_bank_account(current_user.id, company_id)

                flash('ลบข้อมูลทั้งหมดเรียบร้อยแล้ว', 'success')
                return redirect(url_for('main.dashboard'))
            except Exception as e:
                db.session.rollback()
                flash(f'เกิดข้อผิดพลาดในการลบข้อมูล: {str(e)}', 'error')
        else:
            flash('กรุณาพิมพ์ข้อความยืนยันให้ถูกต้อง', 'error')

    # นับจำนวนข้อมูลเพื่อแสดงให้ผู้ใช้เห็น
    transaction_count = Transaction.query.filter_by(company_id=company_id).count()
    import_count = ImportHistory.query.filter_by(company_id=company_id).count()

    return render_template('settings/clear_data.html',
                           transaction_count=transaction_count,
                           import_count=import_count)


@settings_bp.route('/categories/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_category(id):
    # ดึงบริษัทที่ active
    active_company = UserCompany.query.filter_by(
        user_id=current_user.id,
        active_company=True
    ).first()

    if not active_company:
        flash('ไม่พบข้อมูลบริษัทที่ใช้งานอยู่', 'error')
        return redirect(url_for('main.dashboard'))

    category = Category.query.get_or_404(id)

    # ตรวจสอบว่าเป็นหมวดหมู่ของบริษัทหรือไม่
    if category.company_id != active_company.company_id:
        flash('คุณไม่มีสิทธิ์แก้ไขหมวดหมู่นี้', 'error')
        return redirect(url_for('settings.categories'))

    form = CategoryForm(obj=category)

    if form.validate_on_submit():
        category.name = form.name.data
        category.type = form.type.data
        category.keywords = form.keywords.data

        db.session.commit()
        flash('แก้ไขหมวดหมู่เรียบร้อยแล้ว', 'success')
        return redirect(url_for('settings.categories'))

    return render_template('settings/category_form.html', form=form, title='แก้ไขหมวดหมู่')


@settings_bp.route('/categories/delete/<int:id>')
@login_required
def delete_category(id):
    # ดึงบริษัทที่ active
    active_company = UserCompany.query.filter_by(
        user_id=current_user.id,
        active_company=True
    ).first()

    if not active_company:
        flash('ไม่พบข้อมูลบริษัทที่ใช้งานอยู่', 'error')
        return redirect(url_for('main.dashboard'))

    category = Category.query.get_or_404(id)

    # ตรวจสอบว่าเป็นหมวดหมู่ของบริษัทหรือไม่
    if category.company_id != active_company.company_id:
        flash('คุณไม่มีสิทธิ์ลบหมวดหมู่นี้', 'error')
        return redirect(url_for('settings.categories'))

    # ตรวจสอบว่ามี transactions ที่ใช้หมวดหมู่นี้หรือไม่
    transaction_count = Transaction.query.filter_by(category_id=id).count()
    if transaction_count > 0:
        flash(f'ไม่สามารถลบหมวดหมู่นี้ได้ เนื่องจากมีธุรกรรม {transaction_count} รายการที่ใช้หมวดหมู่นี้', 'error')
        return redirect(url_for('settings.categories'))

    db.session.delete(category)
    db.session.commit()
    flash('ลบหมวดหมู่เรียบร้อยแล้ว', 'success')

    return redirect(url_for('settings.categories'))


from datetime import date


# @settings_bp.route('/users')
# @login_required
# def users():
#     # ตรวจสอบว่ามี company_id หรือไม่
#     if not current_user.company_id:
#         # ถ้าไม่มี ให้สร้างบริษัทใหม่
#         company = Company(
#             name=f"บริษัทของ {current_user.name or 'ผู้ใช้ใหม่'}",
#             created_at=datetime.now(bangkok_tz),
#             owner_id=current_user.id
#         )
#         db.session.add(company)
#         db.session.commit()
#
#         # อัปเดตผู้ใช้ให้มี company_id
#         current_user.company_id = company.id
#         db.session.commit()
#     else:
#         # ถ้ามี company_id ให้ดึงข้อมูลบริษัท
#         company = Company.query.get(current_user.company_id)
#
#     # ดึงข้อมูลสมาชิกในบริษัท
#     members = User.query.filter_by(company_id=current_user.company_id).all()
#
#     # ดึงข้อมูลคำเชิญที่ยังไม่ได้ใช้
#     pending_invites = InviteToken.query.filter_by(
#         company_id=current_user.company_id,
#         used=False
#     ).order_by(InviteToken.created_at.desc()).all()
#
#     # ส่งวันที่ปัจจุบันไปด้วย
#     today = date.today()
#
#     return render_template('settings/users.html',
#                            company=company,  # เพิ่มตัวแปร company
#                            members=members,
#                            invite_tokens=pending_invites,
#                            today=today)


# เพิ่มเส้นทางสำหรับจัดการสมาชิกบริษัทใน app/routes/settings.py

@settings_bp.route('/company_members')
@login_required
def company_members():
    """แสดงหน้าจัดการผู้ใช้"""
    # ดึงบริษัทที่ active
    active_company = UserCompany.query.filter_by(
        user_id=current_user.id,
        active_company=True
    ).first()

    if not active_company:
        flash('ไม่พบข้อมูลบริษัทที่ใช้งานอยู่', 'error')
        return redirect(url_for('main.dashboard'))

    company = Company.query.get(active_company.company_id)

    # ดึงข้อมูลสมาชิกในบริษัท
    user_companies = UserCompany.query.filter_by(company_id=company.id).all()
    members = [uc.user for uc in user_companies]

    # ดึงข้อมูลคำเชิญที่ยังไม่ได้ใช้
    pending_invites = InviteToken.query.filter_by(
        company_id=company.id,
        used=False
    ).order_by(InviteToken.created_at.desc()).all()

    return render_template('settings/company_members.html',
                           company=company,
                           members=members,
                           pending_invites=pending_invites)


@settings_bp.route('/remove_member/<int:id>')
@login_required
def remove_member(id):
    # ดึงบริษัทที่ active
    active_company = UserCompany.query.filter_by(
        user_id=current_user.id,
        active_company=True
    ).first()

    if not active_company:
        flash('ไม่พบข้อมูลบริษัทที่ใช้งานอยู่', 'error')
        return redirect(url_for('main.dashboard'))

    company = Company.query.get(active_company.company_id)

    # ตรวจสอบว่าผู้ใช้ปัจจุบันเป็นเจ้าของบริษัทหรือไม่
    if company.owner_id != current_user.id:
        flash('คุณไม่มีสิทธิ์ดำเนินการนี้', 'error')
        return redirect(url_for('settings.company_members'))

    # ไม่อนุญาตให้ลบตัวเอง
    if id == current_user.id:
        flash('คุณไม่สามารถลบตัวเองได้', 'error')
        return redirect(url_for('settings.company_members'))

    # ค้นหาความสัมพันธ์ระหว่างผู้ใช้กับบริษัท
    user_company = UserCompany.query.filter_by(
        user_id=id,
        company_id=company.id
    ).first_or_404()

    # ดึงข้อมูลผู้ใช้
    user = User.query.get(id)

    # สร้างบริษัทใหม่สำหรับผู้ใช้ที่ถูกลบ
    new_company = Company(
        name=f"บริษัทของ {user.name or 'ผู้ใช้'}",
        created_at=datetime.now(bangkok_tz),
        owner_id=user.id
    )
    db.session.add(new_company)
    db.session.commit()

    # ลบความสัมพันธ์เดิม
    db.session.delete(user_company)

    # สร้างความสัมพันธ์ใหม่กับบริษัทใหม่
    new_user_company = UserCompany(
        user_id=id,
        company_id=new_company.id,
        is_admin=True,
        active_company=True
    )
    db.session.add(new_user_company)
    db.session.commit()

    flash(f'ลบ {user.name} ออกจากบริษัทเรียบร้อยแล้ว', 'success')
    return redirect(url_for('settings.company_members'))


# สำหรับอนาคต: ฟังก์ชันตั้ง/ถอดถอนแอดมิน
@settings_bp.route('/toggle_admin/<int:id>')
@login_required
def toggle_admin(id):
    # ดึงบริษัทที่ active
    active_company = UserCompany.query.filter_by(
        user_id=current_user.id,
        active_company=True
    ).first()

    if not active_company:
        flash('ไม่พบข้อมูลบริษัทที่ใช้งานอยู่', 'error')
        return redirect(url_for('main.dashboard'))

    company = Company.query.get(active_company.company_id)

    # ตรวจสอบว่าผู้ใช้ปัจจุบันเป็นเจ้าของบริษัทหรือไม่
    if company.owner_id != current_user.id:
        flash('คุณไม่มีสิทธิ์ดำเนินการนี้', 'error')
        return redirect(url_for('settings.company_members'))

    # ค้นหาความสัมพันธ์ระหว่างผู้ใช้กับบริษัท
    user_company = UserCompany.query.filter_by(
        user_id=id,
        company_id=company.id
    ).first_or_404()

    if not user_company:
        flash('ไม่พบผู้ใช้ในบริษัทนี้', 'error')
        return redirect(url_for('settings.company_members'))

    # สลับสถานะแอดมิน
    user_company.is_admin = not user_company.is_admin
    db.session.commit()

    # ดึงข้อมูลผู้ใช้
    user = User.query.get(id)

    flash(
        f'{"ตั้ง" if user_company.is_admin else "ถอดถอน"} {user.name} {"เป็น" if user_company.is_admin else "จาก"}แอดมินเรียบร้อยแล้ว',
        'success')
    return redirect(url_for('settings.company_members'))