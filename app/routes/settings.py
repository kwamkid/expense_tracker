# app/routes/settings.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models import db, Category, InviteToken, Transaction, ImportHistory
from app.forms import CompanySettingsForm, CategoryForm
import os
import uuid

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


@settings_bp.route('/invite')
@login_required
def invite():
    # Generate invite link
    token = str(uuid.uuid4())
    invite = InviteToken(
        token=token,
        created_by=current_user.id
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