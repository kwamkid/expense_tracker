# app/views/reports.py
from flask import Blueprint, render_template, request, send_file, make_response, current_app
from flask_login import login_required, current_user
from app.models import Transaction, Category, Account
from app.services.report_service import (
    get_monthly_summary,
    get_category_summary,
    get_transactions_by_date_range,
    get_monthly_trend
)
from app.services.export_service import (
    generate_excel_report,
    generate_pdf_report
)
import io
from datetime import datetime, date, timedelta
import calendar

reports_bp = Blueprint('reports', __name__, url_prefix='/reports')


@reports_bp.route('/monthly')
@login_required
def monthly():
    # รับพารามิเตอร์ปีและเดือน (ถ้าไม่มีให้ใช้เดือนปัจจุบัน)
    year = request.args.get('year', datetime.now().year, type=int)
    month = request.args.get('month', datetime.now().month, type=int)

    # ดึงข้อมูลสรุปรายเดือน
    monthly_summary = get_monthly_summary(current_user.active_organization_id, year, month)

    # ดึงข้อมูลธุรกรรมในเดือนที่เลือก
    start_date = date(year, month, 1)
    if month == 12:
        end_date = date(year + 1, 1, 1) - timedelta(days=1)
    else:
        end_date = date(year, month + 1, 1) - timedelta(days=1)

    transactions = get_transactions_by_date_range(current_user.active_organization_id, start_date, end_date)

    # ดึงข้อมูลสรุปตามหมวดหมู่
    category_summary = get_category_summary(current_user.active_organization_id, year, month)

    # สร้างตัวเลือกปีและเดือนสำหรับตัวเลือกในฟอร์ม
    current_year = datetime.now().year
    years = list(range(current_year - 5, current_year + 1))
    months = [(i, calendar.month_name[i]) for i in range(1, 13)]

    return render_template(
        'reports/monthly.html',
        monthly_summary=monthly_summary,
        transactions=transactions,
        category_summary=category_summary,
        year=year,
        month=month,
        years=years,
        months=months,
        title=f'รายงานประจำเดือน {calendar.month_name[month]} {year}'
    )


@reports_bp.route('/category')
@login_required
def category():
    # รับพารามิเตอร์ปี, เดือน และประเภท
    year = request.args.get('year', datetime.now().year, type=int)
    month = request.args.get('month', 0, type=int)  # 0 = ทั้งปี
    transaction_type = request.args.get('type', 'expense')

    # ดึงข้อมูลสรุปตามหมวดหมู่
    category_summary = get_category_summary(current_user.active_organization_id, year, month, transaction_type)

    # สร้างตัวเลือกปีและเดือนสำหรับตัวเลือกในฟอร์ม
    current_year = datetime.now().year
    years = list(range(current_year - 5, current_year + 1))
    months = [(0, 'ทั้งปี')] + [(i, calendar.month_name[i]) for i in range(1, 13)]

    return render_template(
        'reports/category.html',
        category_summary=category_summary,
        year=year,
        month=month,
        type=transaction_type,
        years=years,
        months=months,
        title='รายงานตามหมวดหมู่'
    )


@reports_bp.route('/trends')
@login_required
def trends():
    # รับพารามิเตอร์ปีและจำนวนเดือนที่ต้องการดู
    year = request.args.get('year', datetime.now().year, type=int)
    months_count = request.args.get('months', 12, type=int)

    # ดึงข้อมูลแนวโน้มรายเดือน
    monthly_trend = get_monthly_trend(current_user.active_organization_id, months=months_count, end_year=year)

    # สร้างตัวเลือกปีสำหรับตัวเลือกในฟอร์ม
    current_year = datetime.now().year
    years = list(range(current_year - 5, current_year + 1))

    return render_template(
        'reports/trends.html',
        monthly_trend=monthly_trend,
        year=year,
        months_count=months_count,
        years=years,
        title='แนวโน้มรายรับรายจ่าย'
    )


@reports_bp.route('/export/<report_type>')
@login_required
def export(report_type):
    # รับพารามิเตอร์
    format = request.args.get('format', 'excel')  # 'excel' หรือ 'pdf'

    # สร้างชื่อไฟล์
    if report_type == 'monthly':
        year = request.args.get('year', datetime.now().year, type=int)
        month = request.args.get('month', datetime.now().month, type=int)
        filename = f"monthly_report_{year}_{month}"

        # ดึงข้อมูลสำหรับรายงาน
        monthly_summary = get_monthly_summary(current_user.active_organization_id, year, month)

        start_date = date(year, month, 1)
        if month == 12:
            end_date = date(year + 1, 1, 1) - timedelta(days=1)
        else:
            end_date = date(year, month + 1, 1) - timedelta(days=1)

        transactions = get_transactions_by_date_range(current_user.active_organization_id, start_date, end_date)

        data = {
            'summary': monthly_summary,
            'transactions': transactions,
            'title': f"รายงานประจำเดือน {calendar.month_name[month]} {year}"
        }

    elif report_type == 'category':
        year = request.args.get('year', datetime.now().year, type=int)
        month = request.args.get('month', 0, type=int)
        transaction_type = request.args.get('type', 'expense')

        filename = f"category_report_{year}"
        if month > 0:
            filename += f"_{month}"

        # ดึงข้อมูลสำหรับรายงาน
        category_summary = get_category_summary(current_user.active_organization_id, year, month, transaction_type)

        data = {
            'category_summary': category_summary,
            'title': "รายงานตามหมวดหมู่"
        }

    else:
        return "Invalid report type", 400

    # สร้างรายงานตามฟอร์แมตที่เลือก
    if format == 'excel':
        output = generate_excel_report(data, report_type)
        mimetype = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        filename += '.xlsx'
    else:  # pdf
        output = generate_pdf_report(data, report_type)
        mimetype = 'application/pdf'
        filename += '.pdf'

    # ส่งไฟล์กลับให้ผู้ใช้
    return send_file(
        io.BytesIO(output),
        as_attachment=True,
        download_name=filename,
        mimetype=mimetype
    )