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
    income_categories = Category.query.filter_by(user_id=current_user.id, type='income').all()
    expense_categories = Category.query.filter_by(user_id=current_user.id, type='expense').all()

    return render_template(
        'categories/index.html',
        income_categories=income_categories,
        expense_categories=expense_categories,
        title='หมวดหมู่'
    )


@categories_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    form = CategoryForm()

    if form.validate_on_submit():
        category = Category(
            name=form.name.data,
            type=form.type.data,
            color=form.color.data,
            icon=form.icon.data,
            user_id=current_user.id
        )
        db.session.add(category)
        db.session.commit()

        flash('เพิ่มหมวดหมู่สำเร็จ!', 'success')
        return redirect(url_for('categories.index'))

    return render_template('categories/create.html', form=form, title='เพิ่มหมวดหมู่')


@categories_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    category = Category.query.filter_by(id=id, user_id=current_user.id).first_or_404()
    form = CategoryForm(obj=category)

    if form.validate_on_submit():
        category.name = form.name.data
        category.type = form.type.data
        category.color = form.color.data
        category.icon = form.icon.data

        db.session.commit()
        flash('แก้ไขหมวดหมู่สำเร็จ!', 'success')
        return redirect(url_for('categories.index'))

    return render_template('categories/edit.html', form=form, category=category, title='แก้ไขหมวดหมู่')


@categories_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    category = Category.query.filter_by(id=id, user_id=current_user.id).first_or_404()

    # ตรวจสอบว่ามีธุรกรรมในหมวดหมู่หรือไม่
    if category.transactions.count() > 0:
        flash('ไม่สามารถลบหมวดหมู่ที่มีธุรกรรมได้', 'danger')
        return redirect(url_for('categories.index'))

    db.session.delete(category)
    db.session.commit()

    flash('ลบหมวดหมู่สำเร็จ!', 'success')
    return redirect(url_for('categories.index'))


# app/views/categories.py - เพิ่มเส้นทางสำหรับรีเซ็ตหมวดหมู่

@categories_bp.route('/reset-defaults', methods=['POST'])
@login_required
def reset_defaults():
    """รีเซ็ตหมวดหมู่เริ่มต้น ลบรายการเดิมและสร้างใหม่"""
    try:
        # ตรวจสอบว่ามีธุรกรรมที่ใช้หมวดหมู่หรือไม่
        from app.models import Transaction
        transactions_count = Transaction.query.filter_by(user_id=current_user.id).count()

        if transactions_count > 0:
            flash('ไม่สามารถรีเซ็ตหมวดหมู่ได้ เนื่องจากมีธุรกรรมที่ใช้หมวดหมู่อยู่ กรุณาลบธุรกรรมก่อน', 'danger')
            return redirect(url_for('categories.index'))

        # ลบหมวดหมู่เดิมทั้งหมด
        Category.query.filter_by(user_id=current_user.id).delete()

        # สร้างหมวดหมู่เริ่มต้นใหม่
        from app.views.auth import create_default_categories
        create_default_categories(current_user.id)

        flash('รีเซ็ตหมวดหมู่เป็นค่าเริ่มต้นเรียบร้อยแล้ว', 'success')
    except Exception as e:
        current_app.logger.error(f"Error resetting categories: {str(e)}")
        db.session.rollback()
        flash('เกิดข้อผิดพลาดในการรีเซ็ตหมวดหมู่', 'danger')

    return redirect(url_for('categories.index'))