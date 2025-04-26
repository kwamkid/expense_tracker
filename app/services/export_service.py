# app/services/export_service.py
import io
import xlsxwriter
from flask import render_template
import pdfkit
from datetime import datetime


def generate_excel_report(data, report_type):
    """สร้างรายงาน Excel"""
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output)

    # กำหนด formats
    header_format = workbook.add_format({
        'bold': True,
        'bg_color': '#F7F7F7',
        'border': 1
    })

    number_format = workbook.add_format({
        'num_format': '#,##0.00',
        'border': 1
    })

    date_format = workbook.add_format({
        'num_format': 'dd/mm/yyyy',
        'border': 1
    })

    text_format = workbook.add_format({
        'border': 1
    })

    if report_type == 'monthly':
        worksheet = workbook.add_worksheet('Monthly Report')

        # หัวข้อรายงาน
        worksheet.write(0, 0, data['title'], workbook.add_format({'bold': True, 'font_size': 14}))
        worksheet.write(2, 0, 'สรุปรายรับรายจ่าย', workbook.add_format({'bold': True}))

        # สรุปรายรับรายจ่าย
        summary = data['summary']
        worksheet.write(4, 0, 'รายรับ:', text_format)
        worksheet.write(4, 1, summary['income'], number_format)
        worksheet.write(5, 0, 'รายจ่าย:', text_format)
        worksheet.write(5, 1, summary['expense'], number_format)
        worksheet.write(6, 0, 'คงเหลือ:', text_format)
        worksheet.write(6, 1, summary['balance'], number_format)

        # รายการธุรกรรม
        worksheet.write(8, 0, 'รายการธุรกรรม', workbook.add_format({'bold': True}))

        # หัวตาราง
        headers = ['วันที่', 'ประเภท', 'หมวดหมู่', 'บัญชี', 'รายละเอียด', 'จำนวนเงิน']
        for col, header in enumerate(headers):
            worksheet.write(10, col, header, header_format)

        # ข้อมูลในตาราง
        row = 11
        for transaction in data['transactions']:
            worksheet.write(row, 0, transaction.transaction_date, date_format)
            worksheet.write(row, 1, 'รายรับ' if transaction.type == 'income' else 'รายจ่าย', text_format)
            worksheet.write(row, 2, transaction.category.name, text_format)
            worksheet.write(row, 3, transaction.account.name, text_format)
            worksheet.write(row, 4, transaction.description or '', text_format)
            worksheet.write(row, 5, transaction.amount, number_format)
            row += 1

        # ปรับความกว้างคอลัมน์
        worksheet.set_column(0, 0, 12)  # วันที่
        worksheet.set_column(1, 1, 10)  # ประเภท
        worksheet.set_column(2, 2, 15)  # หมวดหมู่
        worksheet.set_column(3, 3, 15)  # บัญชี
        worksheet.set_column(4, 4, 30)  # รายละเอียด
        worksheet.set_column(5, 5, 12)  # จำนวนเงิน

    elif report_type == 'category':
        worksheet = workbook.add_worksheet('Category Report')

        # หัวข้อรายงาน
        worksheet.write(0, 0, data['title'], workbook.add_format({'bold': True, 'font_size': 14}))

        # หัวตาราง
        headers = ['หมวดหมู่', 'จำนวนเงิน', 'เปอร์เซ็นต์']
        for col, header in enumerate(headers):
            worksheet.write(2, col, header, header_format)

        # คำนวณยอดรวม
        total_amount = sum(cat['total'] for cat in data['category_summary'])

        # ข้อมูลในตาราง
        row = 3
        for category in data['category_summary']:
            worksheet.write(row, 0, category['name'], text_format)
            worksheet.write(row, 1, category['total'], number_format)

            if total_amount > 0:
                percentage = (category['total'] / total_amount) * 100
                worksheet.write(row, 2, f"{percentage:.2f}%", text_format)
            else:
                worksheet.write(row, 2, "0.00%", text_format)

            row += 1

        # ยอดรวม
        worksheet.write(row, 0, 'รวม', workbook.add_format({'bold': True, 'border': 1}))
        worksheet.write(row, 1, total_amount,
                        workbook.add_format({'bold': True, 'num_format': '#,##0.00', 'border': 1}))
        worksheet.write(row, 2, '100.00%', workbook.add_format({'bold': True, 'border': 1}))

        # ปรับความกว้างคอลัมน์
        worksheet.set_column(0, 0, 20)  # หมวดหมู่
        worksheet.set_column(1, 1, 15)  # จำนวนเงิน
        worksheet.set_column(2, 2, 12)  # เปอร์เซ็นต์

    workbook.close()
    return output.getvalue()


def generate_pdf_report(data, report_type):
    """สร้างรายงาน PDF"""
    # ใช้ pdfkit และ wkhtmltopdf สำหรับแปลง HTML เป็น PDF

    if report_type == 'monthly':
        html = render_template(
            'reports/pdf/monthly.html',
            summary=data['summary'],
            transactions=data['transactions'],
            title=data['title'],
            current_date=datetime.now().strftime('%d/%m/%Y')
        )

    elif report_type == 'category':
        # คำนวณยอดรวมและเปอร์เซ็นต์
        total_amount = sum(cat['total'] for cat in data['category_summary'])

        # เพิ่มเปอร์เซ็นต์เข้าไปในข้อมูล
        for category in data['category_summary']:
            if total_amount > 0:
                category['percentage'] = (category['total'] / total_amount) * 100
            else:
                category['percentage'] = 0

        html = render_template(
            'reports/pdf/category.html',
            category_summary=data['category_summary'],
            total_amount=total_amount,
            title=data['title'],
            current_date=datetime.now().strftime('%d/%m/%Y')
        )

    # options สำหรับ wkhtmltopdf
    options = {
        'page-size': 'A4',
        'encoding': 'UTF-8',
        'margin-top': '10mm',
        'margin-right': '10mm',
        'margin-bottom': '10mm',
        'margin-left': '10mm',
    }

    # แปลง HTML เป็น PDF
    pdf = pdfkit.from_string(html, False, options=options)

    return pdf