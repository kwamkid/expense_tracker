from flask import Blueprint, render_template, request, redirect, url_for
from flask_login import login_required, current_user
from app.models import db, Transaction, Category, BankAccount
from sqlalchemy import func
from datetime import datetime, timedelta
import calendar

from flask import jsonify
from dateutil.relativedelta import relativedelta

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('main/landing.html')


# เฉพาะฟังก์ชัน dashboard ใน app/routes/main.py

@main_bp.route('/dashboard')
@login_required
def dashboard():
    # Get current month data (default)
    today = datetime.now()
    first_day = today.replace(day=1)

    # Calculate totals for COMPLETED transactions only
    total_income = db.session.query(func.sum(Transaction.amount)) \
                       .filter_by(user_id=current_user.id, type='income', status='completed') \
                       .filter(Transaction.transaction_date >= first_day) \
                       .scalar() or 0

    total_expense = db.session.query(func.sum(Transaction.amount)) \
                        .filter_by(user_id=current_user.id, type='expense', status='completed') \
                        .filter(Transaction.transaction_date >= first_day) \
                        .scalar() or 0

    balance = total_income - total_expense

    # Get ALL pending transactions (not just current month)
    all_pending_income = db.session.query(func.sum(Transaction.amount)) \
                             .filter_by(user_id=current_user.id, type='income', status='pending') \
                             .scalar() or 0

    all_pending_expense = db.session.query(func.sum(Transaction.amount)) \
                              .filter_by(user_id=current_user.id, type='expense', status='pending') \
                              .scalar() or 0

    # Get recent transactions
    recent_transactions = Transaction.query \
        .filter_by(user_id=current_user.id) \
        .order_by(Transaction.transaction_date.desc(),
                  Transaction.created_at.desc()) \
        .limit(10) \
        .all()

    # Get bank accounts
    bank_accounts = BankAccount.query.filter_by(user_id=current_user.id, is_active=True).all()

    return render_template('main/dashboard.html',
                           total_income=total_income,
                           total_expense=total_expense,
                           balance=balance,
                           all_pending_income=all_pending_income,
                           all_pending_expense=all_pending_expense,
                           recent_transactions=recent_transactions,
                           bank_accounts=bank_accounts)


@main_bp.route('/api/dashboard-data')
@login_required
def dashboard_data_api():
    filter_type = request.args.get('filter', 'this_month')
    start_date = None
    end_date = None

    today = datetime.now()

    # Calculate date range based on filter
    if filter_type == 'this_month':
        start_date = today.replace(day=1)
        end_date = (start_date + relativedelta(months=1)) - timedelta(days=1)

    elif filter_type == 'last_month':
        start_date = (today.replace(day=1) - timedelta(days=1)).replace(day=1)
        end_date = today.replace(day=1) - timedelta(days=1)

    elif filter_type == 'last_3_months':
        start_date = (today - relativedelta(months=3)).replace(day=1)
        end_date = today

    elif filter_type == 'last_6_months':
        start_date = (today - relativedelta(months=6)).replace(day=1)
        end_date = today

    elif filter_type == 'this_year':
        start_date = today.replace(month=1, day=1)
        end_date = today

    elif filter_type == 'last_year':
        start_date = today.replace(year=today.year - 1, month=1, day=1)
        end_date = today.replace(year=today.year - 1, month=12, day=31)

    elif filter_type == 'custom':
        start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d')
        end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d')

    # Calculate totals for the selected period
    total_income = db.session.query(func.sum(Transaction.amount)) \
                       .filter_by(user_id=current_user.id, type='income', status='completed') \
                       .filter(Transaction.transaction_date >= start_date) \
                       .filter(Transaction.transaction_date <= end_date) \
                       .scalar() or 0

    total_expense = db.session.query(func.sum(Transaction.amount)) \
                        .filter_by(user_id=current_user.id, type='expense', status='completed') \
                        .filter(Transaction.transaction_date >= start_date) \
                        .filter(Transaction.transaction_date <= end_date) \
                        .scalar() or 0

    profit_loss = total_income - total_expense

    return jsonify({
        'total_income': float(total_income),
        'total_expense': float(total_expense),
        'profit_loss': float(profit_loss)
    })


@main_bp.route('/reports')
@login_required
def reports():
    # Get date range from query params
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    status_filter = request.args.get('status', 'completed')  # default to completed

    if not start_date:
        start_date = datetime.now().replace(day=1).strftime('%Y-%m-%d')
    if not end_date:
        end_date = datetime.now().strftime('%Y-%m-%d')

    # Get transactions in date range
    query = Transaction.query.filter_by(user_id=current_user.id)

    if status_filter:
        query = query.filter_by(status=status_filter)

    transactions = query.filter(Transaction.transaction_date.between(start_date, end_date)) \
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
        .filter(Transaction.transaction_date.between(start_date, end_date))

    if status_filter:
        category_summary = category_summary.filter(Transaction.status == status_filter)

    category_summary = category_summary.group_by(Category.id).all()

    return render_template('main/reports.html',
                           transactions=transactions,
                           category_summary=category_summary,
                           start_date=start_date,
                           end_date=end_date,
                           total_income=total_income,
                           total_expense=total_expense,
                           status_filter=status_filter)


def get_monthly_data():
    """Get last 6 months data for chart - COMPLETED transactions only"""
    data = []
    today = datetime.now()

    for i in range(5, -1, -1):
        date = today - timedelta(days=i * 30)
        month_start = date.replace(day=1)
        month_end = (month_start + timedelta(days=32)).replace(day=1) - timedelta(days=1)

        income = db.session.query(func.sum(Transaction.amount)) \
                     .filter_by(user_id=current_user.id, type='income', status='completed') \
                     .filter(Transaction.transaction_date.between(month_start, month_end)) \
                     .scalar() or 0

        expense = db.session.query(func.sum(Transaction.amount)) \
                      .filter_by(user_id=current_user.id, type='expense', status='completed') \
                      .filter(Transaction.transaction_date.between(month_start, month_end)) \
                      .scalar() or 0

        data.append({
            'month': calendar.month_name[date.month][:3],
            'income': float(income),
            'expense': float(expense)
        })

    return data