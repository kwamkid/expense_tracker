from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app.models import db, Transaction, Category
from app.forms import TransactionForm
from datetime import datetime

transactions_bp = Blueprint('transactions', __name__, url_prefix='/transactions')


@transactions_bp.route('/')
@login_required
def index():
    page = request.args.get('page', 1, type=int)
    per_page = 20

    query = Transaction.query.filter_by(user_id=current_user.id)

    # Apply filters
    transaction_type = request.args.get('type')
    category_id = request.args.get('category')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if transaction_type:
        query = query.filter_by(type=transaction_type)
    if category_id:
        query = query.filter_by(category_id=category_id)
    if start_date:
        query = query.filter(Transaction.transaction_date >= start_date)
    if end_date:
        query = query.filter(Transaction.transaction_date <= end_date)

    transactions = query.order_by(Transaction.transaction_date.desc()) \
        .paginate(page=page, per_page=per_page)

    categories = Category.query.filter_by(user_id=current_user.id).all()

    return render_template('transactions/index.html',
                           transactions=transactions,
                           categories=categories)


@transactions_bp.route('/add', methods=['GET', 'POST'])
@login_required
def add():
    form = TransactionForm()
    form.category_id.choices = [(c.id, c.name) for c in Category.query.filter_by(user_id=current_user.id).all()]

    if form.validate_on_submit():
        transaction = Transaction(
            amount=form.amount.data,
            description=form.description.data,
            transaction_date=form.transaction_date.data,
            type=form.type.data,
            category_id=form.category_id.data,
            user_id=current_user.id
        )
        db.session.add(transaction)
        db.session.commit()

        flash(f'เพิ่ม{form.type.data == "income" and "รายรับ" or "รายจ่าย"}เรียบร้อยแล้ว', 'success')
        return redirect(url_for('transactions.index'))

    return render_template('transactions/form.html', form=form, title='เพิ่มธุรกรรม')


@transactions_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    transaction = Transaction.query.get_or_404(id)

    if transaction.user_id != current_user.id:
        flash('คุณไม่มีสิทธิ์แก้ไขรายการนี้', 'error')
        return redirect(url_for('transactions.index'))

    form = TransactionForm(obj=transaction)
    form.category_id.choices = [(c.id, c.name) for c in Category.query.filter_by(user_id=current_user.id).all()]

    if form.validate_on_submit():
        transaction.amount = form.amount.data
        transaction.description = form.description.data
        transaction.transaction_date = form.transaction_date.data
        transaction.type = form.type.data
        transaction.category_id = form.category_id.data

        db.session.commit()
        flash('แก้ไขรายการเรียบร้อยแล้ว', 'success')
        return redirect(url_for('transactions.index'))

    return render_template('transactions/form.html', form=form, title='แก้ไขธุรกรรม')


@transactions_bp.route('/delete/<int:id>')
@login_required
def delete(id):
    transaction = Transaction.query.get_or_404(id)

    if transaction.user_id != current_user.id:
        flash('คุณไม่มีสิทธิ์ลบรายการนี้', 'error')
        return redirect(url_for('transactions.index'))

    db.session.delete(transaction)
    db.session.commit()
    flash('ลบรายการเรียบร้อยแล้ว', 'success')

    return redirect(url_for('transactions.index'))