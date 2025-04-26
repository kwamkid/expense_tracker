# app/services/report_service.py
from sqlalchemy import func, extract, and_
from datetime import datetime, date, timedelta
from collections import defaultdict
import calendar
from app.models import Transaction, Category, Account
from app.extensions import db


def get_monthly_summary(user_id, year, month):
    """ดึงข้อมูลสรุปรายรับรายจ่ายประจำเดือน"""
    # กำหนดช่วงวันที่ของเดือน
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)

    # ดึงยอดรวมรายรับ
    income_sum = db.session.query(func.sum(Transaction.amount)) \
                     .filter(
        Transaction.user_id == user_id,
        Transaction.type == 'income',
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date <= end_date
    ).scalar() or 0

    # ดึงยอดรวมรายจ่าย
    expense_sum = db.session.query(func.sum(Transaction.amount)) \
                      .filter(
        Transaction.user_id == user_id,
        Transaction.type == 'expense',
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date <= end_date
    ).scalar() or 0

    return {
        'year': year,
        'month': month,
        'month_name': calendar.month_name[month],
        'start_date': start_date,
        'end_date': end_date,
        'income': income_sum,
        'expense': expense_sum,
        'balance': income_sum - expense_sum
    }


def get_category_summary(user_id, year=None, month=None, transaction_type='expense'):
    """ดึงข้อมูลสรุปตามหมวดหมู่"""
    query = db.session.query(
        Category.id,
        Category.name,
        Category.color,
        Category.icon,
        func.sum(Transaction.amount).label('total')
    ) \
        .join(Transaction, Category.id == Transaction.category_id) \
        .filter(
        Transaction.user_id == user_id,
        Transaction.type == transaction_type
    ) \
        .group_by(Category.id)

    # กรองตามปี/เดือน (ถ้ามี)
    if year:
        query = query.filter(extract('year', Transaction.transaction_date) == year)

    if month and month > 0:
        query = query.filter(extract('month', Transaction.transaction_date) == month)

    # สั่งให้เรียงจากมากไปน้อย
    query = query.order_by(func.sum(Transaction.amount).desc())

    results = query.all()

    # แปลงผลลัพธ์เป็น dict
    categories = []
    for cat_id, name, color, icon, total in results:
        categories.append({
            'id': cat_id,
            'name': name,
            'color': color,
            'icon': icon,
            'total': total
        })

    return categories


def get_recent_transactions(user_id, limit=5):
    """ดึงรายการธุรกรรมล่าสุด"""
    transactions = Transaction.query \
        .filter_by(user_id=user_id) \
        .order_by(Transaction.transaction_date.desc(), Transaction.created_at.desc()) \
        .limit(limit) \
        .all()

    return transactions


def get_account_balances(user_id):
    """ดึงยอดเงินคงเหลือในแต่ละบัญชี"""
    accounts = Account.query \
        .filter_by(user_id=user_id) \
        .order_by(Account.name) \
        .all()

    return accounts


def get_monthly_trend(user_id, months=6, end_year=None, end_month=None):
    """ดึงข้อมูลแนวโน้มรายเดือน"""
    if not end_year:
        end_year = datetime.now().year

    if not end_month:
        end_month = datetime.now().month

    # คำนวณเดือนเริ่มต้น
    if end_month <= months:
        start_year = end_year - 1
        start_month = 12 - (months - end_month)
    else:
        start_year = end_year
        start_month = end_month - months

    # สร้างช่วงวันที่
    if start_month == 12:
        start_date = date(start_year, 12, 1)
    else:
        start_date = date(start_year, start_month + 1, 1)

    if end_month == 12:
        end_date = date(end_year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(end_year, end_month + 1, 1) - timedelta(days=1)

    # ดึงข้อมูลธุรกรรมในช่วงวันที่
    transactions = Transaction.query \
        .filter(
        Transaction.user_id == user_id,
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date <= end_date
    ) \
        .all()

    # จัดกลุ่มตามเดือนและประเภท
    monthly_data = {}

    # สร้างข้อมูลว่างสำหรับทุกเดือน
    current_year = start_year
    current_month = start_month

    for _ in range(months + 1):
        month_key = f"{current_year}-{current_month:02d}"
        monthly_data[month_key] = {
            'year': current_year,
            'month': current_month,
            'month_name': calendar.month_name[current_month],
            'income': 0,
            'expense': 0
        }

        # เลื่อนไปเดือนถัดไป
        if current_month == 12:
            current_year += 1
            current_month = 1
        else:
            current_month += 1

    # เติมข้อมูลจากธุรกรรม
    for transaction in transactions:
        year = transaction.transaction_date.year
        month = transaction.transaction_date.month
        month_key = f"{year}-{month:02d}"

        if month_key in monthly_data:
            if transaction.type == 'income':
                monthly_data[month_key]['income'] += transaction.amount
            else:
                monthly_data[month_key]['expense'] += transaction.amount

    # แปลงจาก dict เป็น list และเรียงตามเดือน
    result = []
    for month_key in sorted(monthly_data.keys()):
        data = monthly_data[month_key]
        data['balance'] = data['income'] - data['expense']
        result.append(data)

    return result


def get_transactions_by_date_range(user_id, start_date, end_date, category_id=None, account_id=None,
                                   transaction_type=None):
    """ดึงรายการธุรกรรมตามช่วงวันที่และเงื่อนไขอื่นๆ"""
    query = Transaction.query \
        .filter(
        Transaction.user_id == user_id,
        Transaction.transaction_date >= start_date,
        Transaction.transaction_date <= end_date
    )

    if category_id:
        query = query.filter(Transaction.category_id == category_id)

    if account_id:
        query = query.filter(Transaction.account_id == account_id)

    if transaction_type:
        query = query.filter(Transaction.type == transaction_type)

    # เรียงตามวันที่ล่าสุด
    query = query.order_by(Transaction.transaction_date.desc())

    return query.all()