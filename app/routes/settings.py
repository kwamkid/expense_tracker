# app/routes/settings.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models import db, Category, InviteToken
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