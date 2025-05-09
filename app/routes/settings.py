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
    # ดึงบริษัทที่ active
    user_company = UserCompany.query.filter_by(user_id=current_user.id, active_company=True).first()

    if not user_company:
        flash('ไม่พบข้อมูลบริษัทที่ใช้งานอยู่', 'error')
        return redirect(url_for('main.dashboard'))

    company_id = user_company.company_id

    # ตรวจสอบว่ามีหมวดหมู่ในบริษัทนี้หรือไม่
    categories = Category.query.filter_by(company_id=company_id).all()

    # ตรวจสอบว่ามีหมวดหมู่ที่ไม่มี company_id หรือไม่
    orphan_categories_count = Category.query.filter(
        Category.user_id == current_user.id,
        (Category.company_id == None) | (Category.company_id != company_id)
    ).count()

    return render_template('settings/categories.html',
                           categories=categories,
                           orphan_categories_count=orphan_categories_count)


@settings_bp.route('/categories/add', methods=['GET', 'POST'])
@login_required
def add_category():
    # ดึงบริษัทที่ active
    user_company = UserCompany.query.filter_by(user_id=current_user.id, active_company=True).first()

    if not user_company:
        flash('ไม่พบข้อมูลบริษัทที่ใช้งานอยู่', 'error')
        return redirect(url_for('main.dashboard'))

    company_id = user_company.company_id

    form = CategoryForm()

    if form.validate_on_submit():
        category = Category(
            name=form.name.data,
            type=form.type.data,
            keywords=form.keywords.data,
            user_id=current_user.id,
            company_id=company_id
        )

        try:
            db.session.add(category)
            db.session.commit()
            flash('เพิ่มหมวดหมู่เรียบร้อยแล้ว', 'success')
            return redirect(url_for('settings.categories'))
        except Exception as e:
            db.session.rollback()
            flash(f'เกิดข้อผิดพลาดในการบันทึกข้อมูล: {str(e)}', 'error')

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

    # สร้างข้อความเชิญที่มีชื่อบริษัท
    company_name = active_company.company.name
    invite_message = f"คุณได้รับเชิญให้เข้าร่วมบริษัท {company_name} - {invite_url}"

    # ส่งคืนเป็น JSON
    return jsonify({
        'success': True,
        'invite_url': invite_url,
        'invite_message': invite_message,
        'company_name': company_name,
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
    user_company = UserCompany.query.filter_by(user_id=current_user.id, active_company=True).first()

    if not user_company:
        flash('ไม่พบข้อมูลบริษัทที่ใช้งานอยู่', 'error')
        return redirect(url_for('main.dashboard'))

    company_id = user_company.company_id

    # Generate invite link
    token = str(uuid.uuid4())
    invite = InviteToken(
        token=token,
        created_by=current_user.id,
        company_id=company_id
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
                # ลำดับการลบข้อมูลสำคัญมาก - ลบ transactions ก่อน แล้วค่อยลบอื่นๆ

                # 1. ลบ Transaction ทั้งหมดที่เกี่ยวข้องกับบริษัทก่อน เพราะมี Foreign Key ไปยัง Categories
                Transaction.query.filter_by(company_id=company_id).delete()
                db.session.commit()

                # 2. ลบ Import History
                ImportHistory.query.filter_by(company_id=company_id).delete()
                db.session.commit()

                # 3. ลบ Categories หลังจากที่ลบ Transaction แล้ว
                Category.query.filter_by(company_id=company_id).delete()
                db.session.commit()

                # 4. ลบ Bank Accounts
                BankAccount.query.filter_by(company_id=company_id).delete()
                db.session.commit()

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
    user_company = UserCompany.query.filter_by(user_id=current_user.id, active_company=True).first()

    if not user_company:
        flash('ไม่พบข้อมูลบริษัทที่ใช้งานอยู่', 'error')
        return redirect(url_for('main.dashboard'))

    company_id = user_company.company_id

    category = Category.query.get_or_404(id)

    # ตรวจสอบว่าเป็นหมวดหมู่ของบริษัทหรือไม่
    if category.company_id != company_id:
        # ถ้าไม่ใช่ แต่เป็นของผู้ใช้ปัจจุบัน ให้ย้ายเข้าบริษัทปัจจุบัน
        if category.user_id == current_user.id:
            category.company_id = company_id
            db.session.commit()
            flash('หมวดหมู่นี้ถูกย้ายเข้าสู่บริษัทปัจจุบันเรียบร้อยแล้ว', 'success')
        else:
            flash('คุณไม่มีสิทธิ์แก้ไขหมวดหมู่นี้', 'error')
            return redirect(url_for('settings.categories'))

    form = CategoryForm(obj=category)

    if form.validate_on_submit():
        # บันทึกข้อมูลก่อนแก้ไข
        old_type = category.type

        # แก้ไขข้อมูล
        category.name = form.name.data
        category.type = form.type.data
        category.keywords = form.keywords.data

        # ตรวจสอบว่ามีการแก้ไข company_id หรือไม่
        if category.company_id != company_id:
            category.company_id = company_id

        # ถ้าแก้ประเภทหมวดหมู่ ต้องตรวจสอบธุรกรรมที่เกี่ยวข้อง
        if old_type != category.type:
            affected_transactions = Transaction.query.filter_by(
                category_id=category.id,
                type=old_type
            ).count()

            if affected_transactions > 0:
                flash(
                    f'คำเตือน: มีรายการธุรกรรม {affected_transactions} รายการที่ใช้หมวดหมู่นี้ การเปลี่ยนประเภทจาก {old_type} เป็น {category.type} อาจทำให้ข้อมูลไม่ตรงกัน',
                    'warning')

        try:
            db.session.commit()
            flash('แก้ไขหมวดหมู่เรียบร้อยแล้ว', 'success')
            return redirect(url_for('settings.categories'))
        except Exception as e:
            db.session.rollback()
            flash(f'เกิดข้อผิดพลาดในการบันทึกข้อมูล: {str(e)}', 'error')

    return render_template('settings/category_form.html', form=form, title='แก้ไขหมวดหมู่')


@settings_bp.route('/categories/delete/<int:id>')
@login_required
def delete_category(id):
    # ดึงบริษัทที่ active
    user_company = UserCompany.query.filter_by(user_id=current_user.id, active_company=True).first()

    if not user_company:
        flash('ไม่พบข้อมูลบริษัทที่ใช้งานอยู่', 'error')
        return redirect(url_for('main.dashboard'))

    company_id = user_company.company_id

    category = Category.query.get_or_404(id)

    # ตรวจสอบว่าเป็นหมวดหมู่ของบริษัทหรือไม่
    if category.company_id != company_id:
        # ถ้าไม่ใช่ แต่เป็นของผู้ใช้ปัจจุบัน
        if category.user_id == current_user.id:
            flash('หมวดหมู่นี้ไม่ได้อยู่ในบริษัทปัจจุบัน หากต้องการลบ กรุณาย้ายเข้าบริษัทปัจจุบันก่อน', 'warning')
        else:
            flash('คุณไม่มีสิทธิ์ลบหมวดหมู่นี้', 'error')
        return redirect(url_for('settings.categories'))

    # ตรวจสอบว่ามี transactions ที่ใช้หมวดหมู่นี้หรือไม่
    transaction_count = Transaction.query.filter_by(category_id=id).count()
    if transaction_count > 0:
        flash(f'ไม่สามารถลบหมวดหมู่นี้ได้ เนื่องจากมีธุรกรรม {transaction_count} รายการที่ใช้หมวดหมู่นี้', 'error')
        return redirect(url_for('settings.categories'))

    try:
        db.session.delete(category)
        db.session.commit()
        flash('ลบหมวดหมู่เรียบร้อยแล้ว', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'เกิดข้อผิดพลาดในการลบหมวดหมู่: {str(e)}', 'error')

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


@settings_bp.route('/fix_categories')
@login_required
def fix_categories():
    """ย้ายหมวดหมู่ที่ยังไม่มี company_id ให้เชื่อมโยงกับบริษัทปัจจุบัน"""
    # ดึงบริษัทที่ active
    user_company = UserCompany.query.filter_by(
        user_id=current_user.id,
        active_company=True
    ).first()

    if not user_company:
        flash('ไม่พบข้อมูลบริษัทที่ใช้งานอยู่', 'error')
        return redirect(url_for('main.dashboard'))

    company_id = user_company.company_id

    # ค้นหาหมวดหมู่ที่มี user_id ตรงกับผู้ใช้ปัจจุบัน แต่ไม่มี company_id
    orphan_categories = Category.query.filter(
        Category.user_id == current_user.id,
        (Category.company_id == None) | (Category.company_id != company_id)
    ).all()

    if not orphan_categories:
        # ถ้าไม่พบหมวดหมู่ที่ต้องแก้ไข ให้ตรวจสอบว่ามีหมวดหมู่ในบริษัทปัจจุบันหรือไม่
        categories = Category.query.filter_by(company_id=company_id).all()
        if not categories:
            # ถ้าไม่มีหมวดหมู่เลย ให้สร้างหมวดหมู่เริ่มต้น
            from app.routes.auth import create_default_categories
            create_default_categories(current_user.id, company_id)
            flash('ระบบได้สร้างหมวดหมู่เริ่มต้นให้แล้ว', 'success')
            return redirect(url_for('settings.categories'))

        flash('ไม่พบหมวดหมู่ที่ต้องแก้ไข', 'info')
        return redirect(url_for('settings.categories'))

    # ย้ายหมวดหมู่ให้เชื่อมโยงกับบริษัทปัจจุบัน
    for category in orphan_categories:
        category.company_id = company_id

    db.session.commit()

    flash(f'ย้ายหมวดหมู่ {len(orphan_categories)} รายการเข้าสู่บริษัทปัจจุบันเรียบร้อยแล้ว', 'success')
    return redirect(url_for('settings.categories'))