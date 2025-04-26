# app/views/dashboard.py
from datetime import datetime, timedelta
from flask import Blueprint, render_template
from flask_login import login_required, current_user
from app.models import Transaction, Account, Category
from app.services.report_service import (
    get_monthly_summary,
    get_category_summary,
    get_recent_transactions,
    get_account_balances,
    get_monthly_trend
)

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def index():
    # ดึงข้อมูลสำหรับ Dashboard

    # 1. ข้อมูลสรุปรายเดือนปัจจุบัน
    current_month = datetime.now().month
    current_year = datetime.now().year
    monthly_summary = get_monthly_summary(current_user.id, current_year, current_month)

    # 2. ข้อมูลสรุปตามหมวดหมู่ (สำหรับ charts)
    category_summary = get_category_summary(current_user.id)

    # 3. ธุรกรรมล่าสุด 5 รายการ
    recent_transactions = get_recent_transactions(current_user.id, limit=5)

    # 4. ยอดเงินคงเหลือในแต่ละบัญชี
    account_balances = get_account_balances(current_user.id)

    # 5. แนวโน้มรายรับ-รายจ่าย 6 เดือนล่าสุด
    monthly_trend = get_monthly_trend(current_user.id, months=6)

    return render_template(
        'dashboard/index.html',
        monthly_summary=monthly_summary,
        category_summary=category_summary,
        recent_transactions=recent_transactions,
        account_balances=account_balances,
        monthly_trend=monthly_trend,
        title='Dashboard'
    )