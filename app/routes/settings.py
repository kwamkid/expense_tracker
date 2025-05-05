# app/routes/settings.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models import db, Category, InviteToken, Transaction, ImportHistory , User , Company
from app.forms import CompanySettingsForm, CategoryForm
import os
import uuid
from datetime import date, datetime  # เพิ่ม datetime ตรงนี้
import pytz  # ต้องเพิ่ม pytz ด้วยเพื่อใช้งาน bangkok_tz

bangkok_tz = pytz.timezone('Asia/Bangkok')
settings_bp = Blueprint('settings', __name__, url_prefix='/settings')


@settings_bp.route('/company', methods=['GET', 'POST'])
@login_required
def company():
    form = CompanySettingsForm(obj=current_user)

    if form.validate_on_submit():
        current_user.company_name = form.company_name.data
        current_user.company_address = form.company_address.data
        current_user.tax_id = form.tax_id.data

        # Handle logo upload
        if form.logo.data:
            file = form.logo.data
            if file and allowed_file(file.filename):
                # Delete old logo
                if current_user.logo_path:
                    old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'logo', current_user.logo_path)
                    if os.path.exists(old_path):
                        os.remove(old_path)

                # Save new logo
                filename = secure_filename(file.filename)
                unique_filename = f"{uuid.uuid4()}_{filename}"
                filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], 'logo', unique_filename)
                file.save(filepath)
                current_user.logo_path = unique_filename

        db.session.commit()
        flash('บันทึกข้อมูลเรียบร้อยแล้ว', 'success')
        return redirect(url_for('settings.company'))

    return render_template('settings/company.html', form=form)


@settings_bp.route('/categories')
@login_required
def categories():
    categories = Category.query.filter_by(user_id=current_user.id).all()
    return render_template('settings/categories.html', categories=categories)


@settings_bp.route('/categories/add', methods=['GET', 'POST'])
@login_required
def add_category():
    form = CategoryForm()

    if form.validate_on_submit():
        category = Category(
            name=form.name.data,
            type=form.type.data,
            keywords=form.keywords.data,
            user_id=current_user.id
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
    # ตรวจสอบว่ามี company_id หรือไม่
    if not current_user.company_id:
        # ถ้าไม่มี ให้สร้างบริษัทใหม่
        company = Company(
            name=f"บริษัทของ {current_user.name or 'ผู้ใช้ใหม่'}",
            created_at=datetime.now(bangkok_tz),
            owner_id=current_user.id
        )
        db.session.add(company)
        db.session.commit()

        # อัปเดตผู้ใช้ให้มี company_id
        current_user.company_id = company.id
        db.session.commit()

    # สร้าง token ใหม่
    token = str(uuid.uuid4())
    invite = InviteToken(
        token=token,
        created_by=current_user.id,
        company_id=current_user.company_id
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
    # ตรวจสอบว่าคำเชิญอยู่ในบริษัทของผู้ใช้หรือไม่
    invite = InviteToken.query.filter_by(
        id=id,
        company_id=current_user.company_id,
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
    # ตรวจสอบว่ามี company_id หรือไม่
    if not current_user.company_id:
        # ถ้าไม่มี ให้สร้างบริษัทใหม่
        company = Company(
            name=f"บริษัทของ {current_user.name or 'ผู้ใช้ใหม่'}",
            created_at=datetime.now(bangkok_tz),
            owner_id=current_user.id
        )
        db.session.add(company)
        db.session.commit()

        # อัปเดตผู้ใช้ให้มี company_id
        current_user.company_id = company.id
        db.session.commit()

    # Generate invite link
    token = str(uuid.uuid4())
    invite = InviteToken(
        token=token,
        created_by=current_user.id,
        company_id=current_user.company_id
    )
    db.session.add(invite)
    db.session.commit()

    invite_url = url_for('auth.login', invite=token, _external=True)
    return render_template('settings/invite.html', invite_url=invite_url)


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in {'png', 'jpg', 'jpeg'}


@settings_bp.route('/clear-data', methods=['GET', 'POST'])
@login_required
def clear_data():
    if request.method == 'POST':
        # ตรวจสอบการยืนยัน
        confirm_text = request.form.get('confirm_text', '')
        if confirm_text.lower() == 'ลบข้อมูลทั้งหมด':
            try:
                # ลบ transactions ทั้งหมดของผู้ใช้
                transactions = Transaction.query.filter_by(user_id=current_user.id).all()
                for transaction in transactions:
                    db.session.delete(transaction)

                # ลบ import history ทั้งหมดของผู้ใช้
                import_histories = ImportHistory.query.filter_by(user_id=current_user.id).all()
                for history in import_histories:
                    db.session.delete(history)

                db.session.commit()
                flash('ลบข้อมูลทั้งหมดเรียบร้อยแล้ว', 'success')
                return redirect(url_for('main.dashboard'))
            except Exception as e:
                db.session.rollback()
                flash(f'เกิดข้อผิดพลาดในการลบข้อมูล: {str(e)}', 'error')
        else:
            flash('กรุณาพิมพ์ข้อความยืนยันให้ถูกต้อง', 'error')

    # นับจำนวนข้อมูลเพื่อแสดงให้ผู้ใช้เห็น
    transaction_count = Transaction.query.filter_by(user_id=current_user.id).count()
    import_count = ImportHistory.query.filter_by(user_id=current_user.id).count()

    return render_template('settings/clear_data.html',
                           transaction_count=transaction_count,
                           import_count=import_count)


@settings_bp.route('/categories/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_category(id):
    category = Category.query.get_or_404(id)

    # ตรวจสอบว่าเป็นหมวดหมู่ของผู้ใช้หรือไม่
    if category.user_id != current_user.id:
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
    category = Category.query.get_or_404(id)

    # ตรวจสอบว่าเป็นหมวดหมู่ของผู้ใช้หรือไม่
    if category.user_id != current_user.id:
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


@settings_bp.route('/users')
@login_required
def users():
    # ดึงข้อมูลผู้ใช้ทั้งหมดในบริษัทเดียวกัน
    users = User.query.filter_by(company_id=current_user.company_id).order_by(User.created_at.desc()).all()

    # ดึงข้อมูล invite tokens ของบริษัท
    invite_tokens = InviteToken.query.filter_by(company_id=current_user.company_id).order_by(InviteToken.created_at.desc()).all()

    # ส่งวันที่ปัจจุบันไปด้วย
    today = date.today()

    return render_template('settings/users.html',
                           users=users,
                           invite_tokens=invite_tokens,
                           today=today)


# เพิ่มเส้นทางสำหรับจัดการสมาชิกบริษัทใน app/routes/settings.py

@settings_bp.route('/company_members')
@login_required
def company_members():
    """แสดงหน้าจัดการผู้ใช้"""
    # ตรวจสอบว่ามี company_id หรือไม่
    if not current_user.company_id:
        # ถ้าไม่มี ให้สร้างบริษัทใหม่
        company = Company(
            name=f"บริษัทของ {current_user.name or 'ผู้ใช้ใหม่'}",
            created_at=datetime.now(bangkok_tz),
            owner_id=current_user.id
        )
        db.session.add(company)
        db.session.commit()

        # อัปเดตผู้ใช้ให้มี company_id
        current_user.company_id = company.id
        db.session.commit()
    else:
        # ถ้ามี company_id ให้ดึงข้อมูลบริษัท
        company = Company.query.get(current_user.company_id)

    # ดึงข้อมูลสมาชิกในบริษัท
    members = User.query.filter_by(company_id=current_user.company_id).all()

    # ดึงข้อมูลคำเชิญที่ยังไม่ได้ใช้
    pending_invites = InviteToken.query.filter_by(
        company_id=current_user.company_id,
        used=False
    ).order_by(InviteToken.created_at.desc()).all()

    return render_template('settings/company_members.html',
                           company=company,
                           members=members,
                           pending_invites=pending_invites)


@settings_bp.route('/remove_member/<int:id>')
@login_required
def remove_member(id):
    # ตรวจสอบว่าผู้ใช้ปัจจุบันเป็นเจ้าของบริษัทหรือไม่
    company = Company.query.get(current_user.company_id)

    if not company or company.owner_id != current_user.id:
        flash('คุณไม่มีสิทธิ์ดำเนินการนี้', 'error')
        return redirect(url_for('settings.company_members'))

    # ไม่อนุญาตให้ลบตัวเอง
    if id == current_user.id:
        flash('คุณไม่สามารถลบตัวเองได้', 'error')
        return redirect(url_for('settings.company_members'))

    # ค้นหาผู้ใช้ที่ต้องการลบ
    user = User.query.filter_by(id=id, company_id=current_user.company_id).first()

    if not user:
        flash('ไม่พบผู้ใช้ในบริษัทนี้', 'error')
        return redirect(url_for('settings.company_members'))

    # สร้างบริษัทใหม่สำหรับผู้ใช้ที่ถูกลบ
    new_company = Company(
        name=f"บริษัทของ {user.name or 'ผู้ใช้'}",
        created_at=datetime.now(bangkok_tz),
        owner_id=user.id
    )
    db.session.add(new_company)
    db.session.commit()

    # ย้ายผู้ใช้ไปยังบริษัทใหม่
    user.company_id = new_company.id
    db.session.commit()

    flash(f'ลบ {user.name} ออกจากบริษัทเรียบร้อยแล้ว', 'success')
    return redirect(url_for('settings.company_members'))


# สำหรับอนาคต: ฟังก์ชันตั้ง/ถอดถอนแอดมิน
@settings_bp.route('/toggle_admin/<int:id>')
@login_required
def toggle_admin(id):
    # ตรวจสอบว่าผู้ใช้ปัจจุบันเป็นเจ้าของบริษัทหรือไม่
    company = Company.query.get(current_user.company_id)

    if not company or company.owner_id != current_user.id:
        flash('คุณไม่มีสิทธิ์ดำเนินการนี้', 'error')
        return redirect(url_for('settings.company_members'))

    # ค้นหาผู้ใช้ที่ต้องการแก้ไข
    user = User.query.filter_by(id=id, company_id=current_user.company_id).first()

    if not user:
        flash('ไม่พบผู้ใช้ในบริษัทนี้', 'error')
        return redirect(url_for('settings.company_members'))

    # สลับสถานะแอดมิน (ต้องเพิ่มฟิลด์ is_admin ในตาราง User ก่อน)
    # user.is_admin = not user.is_admin
    # db.session.commit()

    # flash(f'{"ตั้ง" if user.is_admin else "ถอดถอน"} {user.name} {"เป็น" if user.is_admin else "จาก"}แอดมินเรียบร้อยแล้ว', 'success')
    flash('ฟีเจอร์นี้ยังไม่เปิดให้ใช้งาน', 'info')
    return redirect(url_for('settings.company_members'))