from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify
from flask_login import login_required, current_user
from app.models import db, Transaction, Category, BankAccount, UserCompany
from sqlalchemy import func, case, text
from datetime import datetime, timedelta, date
import calendar
import json

from flask import jsonify
from dateutil.relativedelta import relativedelta

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('main/landing.html')


@main_bp.route('/dashboard')
@login_required
def dashboard():
    # ตรวจสอบและดึงบริษัทที่ active
    user_company = UserCompany.query.filter_by(user_id=current_user.id, active_company=True).first()

    if not user_company:
        flash('ไม่พบข้อมูลบริษัทที่ใช้งานอยู่ กรุณาเลือกบริษัท', 'warning')
        return redirect(url_for('auth.select_company'))

    company_id = user_company.company_id

    # =================== DEBUG: เพิ่มการตรวจสอบ ===================
    print(f"=== DASHBOARD DEBUG ===")
    print(f"Company ID: {company_id}")

    # ตรวจสอบจำนวน transactions ทั้งหมด
    all_transactions = Transaction.query.filter_by(company_id=company_id).all()
    print(f"Total transactions in company: {len(all_transactions)}")

    completed_transactions = Transaction.query.filter_by(company_id=company_id, status='completed').all()
    print(f"Completed transactions: {len(completed_transactions)}")

    # Get current month data (default)
    today = datetime.now().date()  # ใช้ date() เพื่อให้เป็น date object
    first_day = date(today.year, today.month, 1)  # ใช้ date object ตั้งแต่ต้น
    last_day = today

    print(f"Dashboard: Date range for current month: {first_day} to {last_day}")
    print(f"Dashboard: Type of first_day: {type(first_day)}")
    print(f"Dashboard: Type of last_day: {type(last_day)}")

    # ทดสอบการเชื่อมต่อไปยังฐานข้อมูลโดยตรง
    try:
        # SQL ตรง ๆ สำหรับตรวจสอบ
        sql_income = f"""
        SELECT SUM(amount) FROM transaction 
        WHERE company_id = {company_id} 
        AND type = 'income' 
        AND status = 'completed'
        AND transaction_date BETWEEN '{first_day}' AND '{last_day}'
        """

        sql_expense = f"""
        SELECT SUM(amount) FROM transaction 
        WHERE company_id = {company_id} 
        AND type = 'expense' 
        AND status = 'completed'
        AND transaction_date BETWEEN '{first_day}' AND '{last_day}'
        """

        # ดึงข้อมูลด้วย SQL ตรง
        with db.engine.connect() as connection:
            income_result = connection.execute(text(sql_income))
            direct_income_result = income_result.scalar() or 0

            expense_result = connection.execute(text(sql_expense))
            direct_expense_result = expense_result.scalar() or 0

        print(f"Direct SQL query for income: {direct_income_result}")
        print(f"Direct SQL query for expense: {direct_expense_result}")
    except Exception as e:
        print(f"Error in direct SQL query: {str(e)}")
        direct_income_result = 0
        direct_expense_result = 0

    # Calculate totals for COMPLETED transactions only - สำหรับเดือนปัจจุบัน
    try:
        # ลองใช้ between
        total_income_current_month = db.session.query(func.sum(Transaction.amount)) \
                                         .filter_by(company_id=company_id, type='income', status='completed') \
                                         .filter(Transaction.transaction_date.between(first_day, last_day)) \
                                         .scalar() or 0

        total_expense_current_month = db.session.query(func.sum(Transaction.amount)) \
                                          .filter_by(company_id=company_id, type='expense', status='completed') \
                                          .filter(Transaction.transaction_date.between(first_day, last_day)) \
                                          .scalar() or 0

        # เพิ่มการแปลงเป็น float เพื่อให้แน่ใจว่าเป็นตัวเลข
        total_income_current_month = float(total_income_current_month)
        total_expense_current_month = float(total_expense_current_month)

        # ใช้ค่าที่ได้จาก SQL ตรงๆ ถ้าหากค่าเป็น 0
        if total_income_current_month == 0 and direct_income_result > 0:
            total_income_current_month = float(direct_income_result)
            print(f"Using direct SQL result for income: {total_income_current_month}")

        if total_expense_current_month == 0 and direct_expense_result > 0:
            total_expense_current_month = float(direct_expense_result)
            print(f"Using direct SQL result for expense: {total_expense_current_month}")

        # Debug output
        print(f"Income in current month: {total_income_current_month}")
        print(f"Expense in current month: {total_expense_current_month}")
    except Exception as e:
        print(f"Error calculating current month totals: {str(e)}")
        total_income_current_month = 0
        total_expense_current_month = 0

    # คำนวณยอดทั้งหมดโดยไม่จำกัดวันที่ - สำหรับแสดงผลรวมทั้งหมด
    try:
        # SQL สำหรับยอดรวมทั้งหมด
        sql_total_income = f"""
        SELECT SUM(amount) FROM transaction 
        WHERE company_id = {company_id} 
        AND type = 'income' 
        AND status = 'completed'
        """

        sql_total_expense = f"""
        SELECT SUM(amount) FROM transaction 
        WHERE company_id = {company_id} 
        AND type = 'expense' 
        AND status = 'completed'
        """

        with db.engine.connect() as connection:
            total_income_result = connection.execute(text(sql_total_income))
            total_income = total_income_result.scalar() or 0

            total_expense_result = connection.execute(text(sql_total_expense))
            total_expense = total_expense_result.scalar() or 0

        # ลองใช้ SQLAlchemy ORM ด้วย
        orm_total_income = db.session.query(func.sum(Transaction.amount)) \
                               .filter_by(company_id=company_id, type='income', status='completed') \
                               .scalar() or 0

        orm_total_expense = db.session.query(func.sum(Transaction.amount)) \
                                .filter_by(company_id=company_id, type='expense', status='completed') \
                                .scalar() or 0

        print(f"Direct SQL Total Income: {total_income}")
        print(f"Direct SQL Total Expense: {total_expense}")
        print(f"ORM Total Income: {orm_total_income}")
        print(f"ORM Total Expense: {orm_total_expense}")

        # ใช้ค่าที่มากกว่าเป็นหลัก
        total_income = max(float(total_income), float(orm_total_income))
        total_expense = max(float(total_expense), float(orm_total_expense))

    except Exception as e:
        print(f"Error calculating total amounts: {str(e)}")
        total_income = 0
        total_expense = 0

    # แปลงเป็น float
    total_income = float(total_income)
    total_expense = float(total_expense)

    balance_current_month = total_income_current_month - total_expense_current_month
    balance = total_income - total_expense

    print(f"Final Total Income: {total_income}")
    print(f"Final Total Expense: {total_expense}")
    print(f"Final Balance: {balance}")
    print(f"Final Current Month Income: {total_income_current_month}")
    print(f"Final Current Month Expense: {total_expense_current_month}")
    print(f"Final Current Month Balance: {balance_current_month}")

    # Get ALL pending transactions (not just current month)
    all_pending_income = db.session.query(func.sum(Transaction.amount)) \
                             .filter_by(company_id=company_id, type='income', status='pending') \
                             .scalar() or 0

    all_pending_expense = db.session.query(func.sum(Transaction.amount)) \
                              .filter_by(company_id=company_id, type='expense', status='pending') \
                              .scalar() or 0

    print(f"Pending Income: {all_pending_income}")
    print(f"Pending Expense: {all_pending_expense}")

    # ตรวจสอบว่ามี transactions นอกช่วงวันที่เดือนปัจจุบันไหม
    try:
        transactions_outside_current_month = Transaction.query.filter_by(
            company_id=company_id,
            status='completed'
        ).filter(
            (Transaction.transaction_date < first_day) |
            (Transaction.transaction_date > last_day)
        ).count()

        print(f"Transactions outside current month: {transactions_outside_current_month}")

        # ดูยอดของ transactions นอกเดือนปัจจุบัน
        outside_income = db.session.query(func.sum(Transaction.amount)) \
                             .filter_by(company_id=company_id, type='income', status='completed') \
                             .filter(
            (Transaction.transaction_date < first_day) |
            (Transaction.transaction_date > last_day)
        ).scalar() or 0

        outside_expense = db.session.query(func.sum(Transaction.amount)) \
                              .filter_by(company_id=company_id, type='expense', status='completed') \
                              .filter(
            (Transaction.transaction_date < first_day) |
            (Transaction.transaction_date > last_day)
        ).scalar() or 0

        print(f"Income outside current month: {outside_income}")
        print(f"Expense outside current month: {outside_expense}")

    except Exception as e:
        print(f"Error checking transactions outside current month: {str(e)}")

    print("======================")

    # Get recent transactions
    recent_transactions = Transaction.query \
        .filter_by(company_id=company_id) \
        .order_by(Transaction.transaction_date.desc(),
                  Transaction.created_at.desc()) \
        .limit(10) \
        .all()

    # Get bank accounts - แก้ไขให้ดึงตาม company_id แทน user_id
    bank_accounts = BankAccount.query.filter_by(company_id=company_id, is_active=True).all()

    # Get categories for this company
    categories = Category.query.filter_by(company_id=company_id).all()

    # สร้าง dashboard_data เพื่อส่งไปยัง JS
    dashboard_data = {
        'total_income': float(total_income),
        'total_expense': float(total_expense),
        'balance': float(balance),
        'total_income_current_month': float(total_income_current_month),
        'total_expense_current_month': float(total_expense_current_month),
        'balance_current_month': float(balance_current_month)
    }

    # แปลงเป็น JSON สำหรับใช้ใน JS
    dashboard_json = json.dumps(dashboard_data)

    return render_template('main/dashboard.html',
                           total_income=total_income,
                           total_expense=total_expense,
                           balance=balance,
                           total_income_current_month=total_income_current_month,
                           total_expense_current_month=total_expense_current_month,
                           balance_current_month=balance_current_month,
                           all_pending_income=all_pending_income,
                           all_pending_expense=all_pending_expense,
                           recent_transactions=recent_transactions,
                           bank_accounts=bank_accounts,
                           categories=categories,
                           dashboard_json=dashboard_json)  # ส่ง JSON ไปด้วย


@main_bp.route('/api/dashboard-data')
@login_required
def dashboard_data_api():
    # ดึงบริษัทที่ active
    user_company = UserCompany.query.filter_by(user_id=current_user.id, active_company=True).first()

    if not user_company:
        return jsonify({
            'total_income': 0,
            'total_expense': 0,
            'profit_loss': 0
        })

    company_id = user_company.company_id

    filter_type = request.args.get('filter', 'this_month')
    start_date = None
    end_date = None

    today = datetime.now().date()  # ใช้ date() เพื่อให้เป็น date object

    # Calculate date range based on filter
    if filter_type == 'this_month':
        start_date = date(today.year, today.month, 1)
        # คำนวณวันสุดท้ายของเดือน
        if today.month == 12:
            end_date = date(today.year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(today.year, today.month + 1, 1) - timedelta(days=1)

        # Debug output
        print(f"This month date range: {start_date} to {end_date}")

    elif filter_type == 'last_month':
        # First day of previous month
        if today.month == 1:
            start_date = date(today.year - 1, 12, 1)
            end_date = date(today.year, 1, 1) - timedelta(days=1)
        else:
            start_date = date(today.year, today.month - 1, 1)
            end_date = date(today.year, today.month, 1) - timedelta(days=1)

    elif filter_type == 'last_3_months':
        start_date = (today - relativedelta(months=3)).replace(day=1)
        end_date = today

    elif filter_type == 'last_6_months':
        start_date = (today - relativedelta(months=6)).replace(day=1)
        end_date = today

    elif filter_type == 'this_year':
        start_date = date(today.year, 1, 1)
        end_date = today

    elif filter_type == 'last_year':
        start_date = date(today.year - 1, 1, 1)
        end_date = date(today.year - 1, 12, 31)

    elif filter_type == 'custom':
        try:
            start_date = datetime.strptime(request.args.get('start_date'), '%Y-%m-%d').date()
            end_date = datetime.strptime(request.args.get('end_date'), '%Y-%m-%d').date()
        except:
            start_date = date(today.year, today.month, 1)
            end_date = today

    elif filter_type == 'all':
        # ดึงข้อมูลทั้งหมดโดยไม่จำกัดวันที่
        try:
            # SQL ตรง ๆ เพื่อตรวจสอบ
            with db.engine.connect() as connection:
                income_result = connection.execute(text(f"""
                    SELECT SUM(amount) FROM transaction 
                    WHERE company_id = {company_id} 
                    AND type = 'income' 
                    AND status = 'completed'
                """))
                direct_income_result = income_result.scalar() or 0

                expense_result = connection.execute(text(f"""
                    SELECT SUM(amount) FROM transaction 
                    WHERE company_id = {company_id} 
                    AND type = 'expense' 
                    AND status = 'completed'
                """))
                direct_expense_result = expense_result.scalar() or 0

            print(f"Direct SQL query for all income: {direct_income_result}")
            print(f"Direct SQL query for all expense: {direct_expense_result}")

            # ใช้ SQLAlchemy ORM
            total_income = db.session.query(func.sum(Transaction.amount)) \
                               .filter_by(company_id=company_id, type='income', status='completed') \
                               .scalar() or 0

            total_expense = db.session.query(func.sum(Transaction.amount)) \
                                .filter_by(company_id=company_id, type='expense', status='completed') \
                                .scalar() or 0

            # ตรวจสอบค่าและใช้ค่าจาก SQL ตรงๆ ถ้าจำเป็น
            if total_income == 0 and direct_income_result > 0:
                total_income = direct_income_result

            if total_expense == 0 and direct_expense_result > 0:
                total_expense = direct_expense_result

            profit_loss = float(total_income) - float(total_expense)

            # Debug output
            print(f"All time total - Income: {total_income}, Expense: {total_expense}")

            return jsonify({
                'total_income': float(total_income),
                'total_expense': float(total_expense),
                'profit_loss': float(profit_loss)
            })

        except Exception as e:
            print(f"Error in 'all' filter: {str(e)}")
            return jsonify({
                'total_income': 0,
                'total_expense': 0,
                'profit_loss': 0,
                'error': str(e)
            })

    # ระวังกรณีที่ start_date หรือ end_date เป็น None
    if not start_date or not end_date:
        return jsonify({
            'total_income': 0,
            'total_expense': 0,
            'profit_loss': 0,
            'error': 'Invalid date range'
        })

    try:
        # Debug output
        print(f"Filtered date range: {start_date} to {end_date}")

        # ทดสอบด้วย SQL ตรง
        with db.engine.connect() as connection:
            income_result = connection.execute(text(f"""
                SELECT SUM(amount) FROM transaction 
                WHERE company_id = {company_id} 
                AND type = 'income' 
                AND status = 'completed'
                AND transaction_date BETWEEN '{start_date}' AND '{end_date}'
            """))
            direct_income_result = income_result.scalar() or 0

            expense_result = connection.execute(text(f"""
                SELECT SUM(amount) FROM transaction 
                WHERE company_id = {company_id} 
                AND type = 'expense' 
                AND status = 'completed'
                AND transaction_date BETWEEN '{start_date}' AND '{end_date}'
            """))
            direct_expense_result = expense_result.scalar() or 0

        print(f"Direct SQL query for filtered income: {direct_income_result}")
        print(f"Direct SQL query for filtered expense: {direct_expense_result}")

        # ใช้ SQLAlchemy
        total_income_query = db.session.query(func.sum(Transaction.amount)) \
            .filter_by(company_id=company_id, type='income', status='completed') \
            .filter(Transaction.transaction_date.between(start_date, end_date))

        # Debug output
        print(
            f"SQL Query for income: {str(total_income_query.statement.compile(compile_kwargs={'literal_binds': True}))}")

        total_income = total_income_query.scalar() or 0

        total_expense = db.session.query(func.sum(Transaction.amount)) \
                            .filter_by(company_id=company_id, type='expense', status='completed') \
                            .filter(Transaction.transaction_date.between(start_date, end_date)) \
                            .scalar() or 0

        # ตรวจสอบค่าและใช้ค่าจาก SQL ตรงๆ ถ้าจำเป็น
        if total_income == 0 and direct_income_result > 0:
            total_income = direct_income_result
            print(f"Using direct SQL result for filtered income: {total_income}")

        if total_expense == 0 and direct_expense_result > 0:
            total_expense = direct_expense_result
            print(f"Using direct SQL result for filtered expense: {total_expense}")

        profit_loss = float(total_income) - float(total_expense)

        # Debug output
        print(f"Period from {start_date} to {end_date} - Income: {total_income}, Expense: {total_expense}")

        return jsonify({
            'total_income': float(total_income),
            'total_expense': float(total_expense),
            'profit_loss': float(profit_loss)
        })

    except Exception as e:
        print(f"Error in date range filter: {str(e)}")
        return jsonify({
            'total_income': 0,
            'total_expense': 0,
            'profit_loss': 0,
            'error': str(e)
        })


# แก้ไขใน app/routes/main.py - ฟังก์ชัน reports()

@main_bp.route('/reports')
@login_required
def reports():
    # ดึงบริษัทที่ active
    user_company = UserCompany.query.filter_by(user_id=current_user.id, active_company=True).first()

    if not user_company:
        flash('ไม่พบข้อมูลบริษัทที่ใช้งานอยู่ กรุณาเลือกบริษัท', 'warning')
        return redirect(url_for('auth.select_company'))

    company_id = user_company.company_id

    # Get filter parameters
    transaction_type = request.args.get('type')
    category_id = request.args.get('category')
    status_filter = request.args.get('status')
    bank_account_id = request.args.get('bank_account')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    # ===== แก้ไข Status Filter =====
    # ถ้า status_filter เป็นค่าว่าง ให้ตั้งเป็น None
    if status_filter == '':
        status_filter = None
    # ถ้าไม่มีการส่งมาเลย ให้ default เป็น 'completed'
    elif status_filter is None:
        status_filter = 'completed'

    # ===== แก้ไข Category และ Bank Account Filter =====
    if category_id == '':
        category_id = None
    if bank_account_id == '':
        bank_account_id = None
    if transaction_type == '':
        transaction_type = None

    # Default date range - หาจากข้อมูลจริง
    if not start_date or not end_date:
        try:
            date_range = db.session.query(
                func.min(Transaction.transaction_date).label('min_date'),
                func.max(Transaction.transaction_date).label('max_date')
            ).filter_by(company_id=company_id).first()

            if date_range.min_date and date_range.max_date:
                if not start_date:
                    start_date = date_range.min_date.strftime('%Y-%m-%d')
                if not end_date:
                    end_date = date_range.max_date.strftime('%Y-%m-%d')
            else:
                # ถ้าไม่มีข้อมูล ใช้ปีปัจจุบัน
                current_year = datetime.now().year
                start_date = f"{current_year}-01-01"
                end_date = datetime.now().strftime('%Y-%m-%d')
        except Exception as e:
            print(f"Error getting date range: {str(e)}")
            current_year = datetime.now().year
            start_date = f"{current_year}-01-01"
            end_date = datetime.now().strftime('%Y-%m-%d')

    print(f"=== REPORTS DEBUG ===")
    print(f"Company ID: {company_id}")
    print(f"Filter Parameters:")
    print(f"  - Transaction Type: {transaction_type}")
    print(f"  - Category ID: {category_id}")
    print(f"  - Status Filter: {status_filter}")
    print(f"  - Bank Account ID: {bank_account_id}")
    print(f"  - Start Date: {start_date}")
    print(f"  - End Date: {end_date}")

    # ทดสอบด้วย SQL ตรงๆ สำหรับ Reports
    try:
        # SQL สำหรับช่วงวันที่ที่กำหนด - แก้ไขให้รองรับ status_filter = None
        sql_base = f"""
        SELECT SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END) as income,
               SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END) as expense
        FROM transaction 
        WHERE company_id = {company_id}
        AND transaction_date BETWEEN '{start_date}' AND '{end_date}'
        """

        # เพิ่ม status filter ถ้ามี
        if status_filter:
            sql_base += f" AND status = '{status_filter}'"

        # เพิ่ม filter อื่นๆ ถ้ามี
        if transaction_type:
            sql_base += f" AND type = '{transaction_type}'"
        if category_id:
            sql_base += f" AND category_id = {category_id}"
        if bank_account_id:
            sql_base += f" AND bank_account_id = {bank_account_id}"

        print(f"SQL Query: {sql_base}")

        # รัน SQL
        with db.engine.connect() as connection:
            result = connection.execute(text(sql_base))
            row = result.fetchone()
            direct_filtered_income = row[0] or 0
            direct_filtered_expense = row[1] or 0

        print(f"Direct SQL Results:")
        print(f"  - Filtered Income: {direct_filtered_income}")
        print(f"  - Filtered Expense: {direct_filtered_expense}")

    except Exception as e:
        print(f"Error in direct SQL queries: {str(e)}")
        direct_filtered_income = 0
        direct_filtered_expense = 0

    # Build query - ใช้ company_id ในการค้นหา
    query = Transaction.query.filter_by(company_id=company_id)

    base_query_count = query.count()
    print(f"Base query count (company only): {base_query_count}")

    if transaction_type:
        query = query.filter_by(type=transaction_type)
        print(f"After type filter: {query.count()}")

    if category_id:
        query = query.filter_by(category_id=category_id)
        print(f"After category filter: {query.count()}")

    if status_filter:  # ตรวจสอบว่าไม่เป็น None
        query = query.filter_by(status=status_filter)
        print(f"After status filter: {query.count()}")

    if bank_account_id:
        query = query.filter_by(bank_account_id=bank_account_id)
        print(f"After bank account filter: {query.count()}")

    # Apply date range
    query = query.filter(Transaction.transaction_date.between(start_date, end_date))
    print(f"After date range filter: {query.count()}")

    transactions = query.order_by(Transaction.transaction_date.desc()).all()

    print(f"Final filtered transactions count: {len(transactions)}")

    # Calculate totals
    total_income = sum(t.amount for t in transactions if t.type == 'income')
    total_expense = sum(t.amount for t in transactions if t.type == 'expense')
    net_profit = total_income - total_expense

    print(f"ORM Calculated Results:")
    print(f"  - Total Income: {total_income}")
    print(f"  - Total Expense: {total_expense}")
    print(f"  - Net Profit: {net_profit}")

    # เปรียบเทียบกับ SQL ตรงๆ
    print(f"Comparison with Direct SQL:")
    print(f"  - Income diff: {total_income - direct_filtered_income}")
    print(f"  - Expense diff: {total_expense - direct_filtered_expense}")

    print("====================")

    # Category breakdown - แก้ไข status filter
    category_breakdown = db.session.query(
        Category.name,
        Category.type,
        func.sum(Transaction.amount).label('total'),
        func.count(Transaction.id).label('count')
    ).join(Transaction) \
        .filter(Transaction.company_id == company_id) \
        .filter(Transaction.transaction_date.between(start_date, end_date))

    if status_filter:  # ตรวจสอบว่าไม่เป็น None
        category_breakdown = category_breakdown.filter(Transaction.status == status_filter)

    category_breakdown = category_breakdown.group_by(Category.id).all()

    # Bank account breakdown - แก้ไข status filter
    bank_breakdown = db.session.query(
        BankAccount.bank_name,
        BankAccount.account_number,
        func.sum(case(
            (Transaction.type == 'income', Transaction.amount),
            else_=0
        )).label('income'),
        func.sum(case(
            (Transaction.type == 'expense', Transaction.amount),
            else_=0
        )).label('expense'),
        func.count(Transaction.id).label('count')
    ).join(Transaction, Transaction.bank_account_id == BankAccount.id) \
        .filter(Transaction.company_id == company_id) \
        .filter(Transaction.transaction_date.between(start_date, end_date))

    if status_filter:  # ตรวจสอบว่าไม่เป็น None
        bank_breakdown = bank_breakdown.filter(Transaction.status == status_filter)

    bank_breakdown = bank_breakdown.group_by(BankAccount.id).all()

    # Daily summary - แก้ไข status filter
    daily_summary = db.session.query(
        Transaction.transaction_date,
        func.sum(case(
            (Transaction.type == 'income', Transaction.amount),
            else_=0
        )).label('income'),
        func.sum(case(
            (Transaction.type == 'expense', Transaction.amount),
            else_=0
        )).label('expense')
    ).filter(Transaction.company_id == company_id) \
        .filter(Transaction.transaction_date.between(start_date, end_date))

    if status_filter:  # ตรวจสอบว่าไม่เป็น None
        daily_summary = daily_summary.filter(Transaction.status == status_filter)

    daily_summary = daily_summary.group_by(Transaction.transaction_date) \
        .order_by(Transaction.transaction_date).all()

    # Get categories and bank accounts for filters
    categories = Category.query.filter_by(company_id=company_id).all()
    bank_accounts = BankAccount.query.filter_by(company_id=company_id).all()

    return render_template('main/reports.html',
                           transactions=transactions,
                           categories=categories,
                           bank_accounts=bank_accounts,
                           category_breakdown=category_breakdown,
                           bank_breakdown=bank_breakdown,
                           daily_summary=daily_summary,
                           start_date=start_date,
                           end_date=end_date,
                           total_income=total_income,
                           total_expense=total_expense,
                           net_profit=net_profit,
                           status_filter=status_filter,
                           filters=request.args)


def get_monthly_data():
    """Get last 6 months data for chart - COMPLETED transactions only"""
    # ดึงบริษัทที่ active
    user_company = UserCompany.query.filter_by(user_id=current_user.id, active_company=True).first()

    if not user_company:
        return []  # ถ้าไม่มีบริษัทที่ active ให้ส่งคืนลิสต์ว่าง

    company_id = user_company.company_id

    data = []
    today = datetime.now().date()

    for i in range(5, -1, -1):
        date = today - relativedelta(months=i)
        month_start = date.replace(day=1)

        # คำนวณวันสุดท้ายของเดือน
        if month_start.month == 12:
            month_end = date(month_start.year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(month_start.year, month_start.month + 1, 1) - timedelta(days=1)

        # เปลี่ยนจาก user_id เป็น company_id
        income = db.session.query(func.sum(Transaction.amount)) \
                     .filter_by(company_id=company_id, type='income', status='completed') \
                     .filter(Transaction.transaction_date.between(month_start, month_end)) \
                     .scalar() or 0

        expense = db.session.query(func.sum(Transaction.amount)) \
                      .filter_by(company_id=company_id, type='expense', status='completed') \
                      .filter(Transaction.transaction_date.between(month_start, month_end)) \
                      .scalar() or 0

        data.append({
            'month': calendar.month_name[date.month][:3],
            'income': float(income),
            'expense': float(expense)
        })

    return data