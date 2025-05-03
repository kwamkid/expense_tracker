from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from app.models import db, Transaction, Category
from sqlalchemy import func
from datetime import datetime, timedelta
import calendar

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('main/landing.html')


@main_bp.route('/dashboard')
@login_required
def dashboard():
    # Get current month data
    today = datetime.now()
    first_day = today.replace(day=1)

    # Calculate totals
    total_income = db.session.query(func.sum(Transaction.amount)) \
                       .filter_by(user_id=current_user.id, type='income') \
                       .filter(Transaction.transaction_date >= first_day) \
                       .scalar() or 0

    total_expense = db.session.query(func.sum(Transaction.amount)) \
                        .filter_by(user_id=current_user.id, type='expense') \
                        .filter(Transaction.transaction_date >= first_day) \
                        .scalar() or 0

    balance = total_income - total_expense

    # Get recent transactions
    recent_transactions = Transaction.query \
        .filter_by(user_id=current_user.id) \
        .order_by(Transaction.transaction_date.desc()) \
        .limit(10) \
        .all()

    # Get monthly data for chart
    monthly_data = get_monthly_data()

    return render_template('main/dashboard.html',
                           total_income=total_income,
                           total_expense=total_expense,
                           balance=balance,
                           recent_transactions=recent_transactions,
                           monthly_data=monthly_data)


@main_bp.route('/reports')
@login_required
def reports():
    # Get date range from query params
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    if not start_date:
        start_date = datetime.now().replace(day=1).strftime('%Y-%m-%d')
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')

    # Get transactions in date range
    transactions = Transaction.query \
        .filter_by(user_id=current_user.id) \
        .filter(Transaction.transaction_date.between(start_date, end_date)) \
        .order_by(Transaction.transaction_date.desc()) \
        .all()

    # Calculate totals
    total_income = sum(t.amount for t in transactions if t.type == 'income')
    total_expense = sum(t.amount for t in transactions if t.type == 'expense')

    # Calculate category summaries
    category_summary = db.session.query(
        Category.name,
        Category.type,
        func.sum(Transaction.amount).label('total')
    ).join(Transaction) \
        .filter(Transaction.user_id == current_user.id) \
        .filter(Transaction.transaction_date.between(start_date, end_date)) \
        .group_by(Category.id) \
        .all()

    return render_template('main/reports.html',
                           transactions=transactions,
                           category_summary=category_summary,
                           start_date=start_date,
                           end_date=end_date,
                           total_income=total_income,
                           total_expense=total_expense)


def get_monthly_data():
    """Get last 6 months data for chart"""
    data = []
    today = datetime.now()

    for i in range(5, -1, -1):
        date = today - timedelta(days=i * 30)
        month_start = date.replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        income = db.session.query(func.sum(Transaction.amount)) \
                     .filter_by(user_id=current_user.id, type='income') \
                     .filter(Transaction.transaction_date.between(month_start, month_end)) \
                     .scalar() or 0

        expense = db.session.query(func.sum(Transaction.amount)) \
                      .filter_by(user_id=current_user.id, type='expense') \
                      .filter(Transaction.transaction_date.between(month_start, month_end)) \
                      .scalar() or 0

        data.append({
            'month': calendar.month_name[date.month][:3],
            'income': float(income),
            'expense': float(expense)
        })

    return data