# app/views/categories.py
from flask import Blueprint, render_template, redirect, url_for, flash, request , current_app
from flask_login import login_required, current_user
from app.forms.category import CategoryForm
from app.models import Category
from app.extensions import db

categories_bp = Blueprint('categories', __name__, url_prefix='/categories')


@categories_bp.route('/')
@login_required
def index():
    # แยกหมวดหมู่ตามประเภท
    income_categories = Category.query.filter_by(organization_id=current_user.active_organization_id, type='income').all()
    expense_categories = Category.query.filter_by(organization_id=current_user.active_organization_id, type='expense').all()

    return render_template(
        'categories/index.html',
        income_categories=income_categories,
        expense_categories=expense_categories,
        title='หมวดหมู่'
    )


@categories_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    # รับค่า type จาก query string (ถ้ามี)
    category_type = request.args.get('type', 'expense')
    form = CategoryForm()

    # กำหนดค่าเริ่มต้นของประเภทหมวดหมู่
    if category_type and category_type in ['income', 'expense']:
        form.type.data = category_type

    if form.validate_on_submit():
        category = Category(
            name=form.name.data,
            type=form.type.data,
            color=form.color.data,
            icon=form.icon.data,
            organization_id=current_user.active_organization_id,
            created_by=current_user.id,  # เพิ่มการกำหนดค่า created_by
            updated_by=current_user.id  # เพิ่มการกำหนดค่า updated_by
        )

        db.session.add(category)
        db.session.commit()

        flash(f'เพิ่มหมวดหมู่ "{form.name.data}" สำเร็จ!', 'success')
        return redirect(url_for('categories.index'))

    return render_template(
        'categories/create.html',
        form=form,
        title='เพิ่มหมวดหมู่ใหม่',
        category_type=category_type
    )


@categories_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    category = Category.query.filter_by(id=id, organization_id=current_user.active_organization_id).first_or_404()
    form = CategoryForm(obj=category)

    if form.validate_on_submit():
        category.name = form.name.data
        category.type = form.type.data
        category.color = form.color.data
        category.icon = form.icon.data
        category.updated_by = current_user.id  # เพิ่มบรรทัดนี้

        db.session.commit()
        flash(f'แก้ไขหมวดหมู่ "{form.name.data}" สำเร็จ!', 'success')
        return redirect(url_for('categories.index'))

    return render_template('categories/edit.html', form=form, category=category, title='แก้ไขหมวดหมู่')


@categories_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    category = Category.query.filter_by(id=id, organization_id=current_user.active_organization_id).first_or_404()

    # ตรวจสอบว่ามีธุรกรรมในหมวดหมู่หรือไม่
    if category.transactions.count() > 0:
        flash('ไม่สามารถลบหมวดหมู่ที่มีธุรกรรมได้', 'danger')
        return redirect(url_for('categories.index'))

    db.session.delete(category)
    db.session.commit()

    flash('ลบหมวดหมู่สำเร็จ!', 'success')
    return redirect(url_for('categories.index'))


# app/views/categories.py - เพิ่มเส้นทางสำหรับรีเซ็ตหมวดหมู่

@categories_bp.route('/reset_defaults', methods=['POST'])
@login_required
def reset_defaults():
    # ตรวจสอบว่ามีหมวดหมู่ที่มีธุรกรรมอยู่หรือไม่
    categories_with_transactions = Category.query.filter(
        Category.organization_id == current_user.active_organization_id,
        Category.transactions.any()
    ).all()

    if categories_with_transactions:
        flash('ไม่สามารถรีเซ็ตหมวดหมู่ได้เนื่องจากมีหมวดหมู่ที่มีธุรกรรมอยู่ กรุณาลบธุรกรรมก่อน', 'danger')
        return redirect(url_for('categories.index'))

    try:
        # ลบหมวดหมู่ทั้งหมดของ organization นี้
        Category.query.filter_by(organization_id=current_user.active_organization_id).delete()

        # สร้างหมวดหมู่เริ่มต้น
        from app.views.auth import create_default_categories
        create_default_categories(current_user.active_organization_id, current_user.id)

        db.session.commit()
        flash('รีเซ็ตหมวดหมู่เป็นค่าเริ่มต้นสำเร็จ!', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'เกิดข้อผิดพลาดในการรีเซ็ตหมวดหมู่: {str(e)}', 'danger')

    return redirect(url_for('categories.index'))