# app/routes/imports.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models import db, Transaction, Category, ImportHistory, BankAccount, UserCompany
from app.services.import_service import BankImportService
from app.services.category_matcher import CategoryMatcher
from app.services.balance_service import BalanceService
import os
import json
import uuid
from datetime import datetime
import pytz

imports_bp = Blueprint('imports', __name__, url_prefix='/imports')
bangkok_tz = pytz.timezone('Asia/Bangkok')


def allowed_file(filename):
    """Check if the file has an allowed extension"""
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in {'xlsx', 'xls'}


@imports_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
        # ดึงบริษัทที่ active
        user_company = UserCompany.query.filter_by(
            user_id=current_user.id,
            active_company=True
        ).first()

        if not user_company:
            flash('ไม่พบข้อมูลบริษัทที่ใช้งานอยู่', 'error')
            return redirect(url_for('main.dashboard'))

        company_id = user_company.company_id

        if 'file' not in request.files:
            flash('กรุณาเลือกไฟล์', 'error')
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            flash('กรุณาเลือกไฟล์', 'error')
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)

            # Save the file
            file.save(filepath)

            # เก็บชื่อไฟล์ต้นฉบับไว้ใน session
            session['original_filename'] = file.filename

            # Process file
            bank_type = request.form.get('bank_type')
            bank_account_id = request.form.get('bank_account_id')

            if not bank_account_id:
                flash('กรุณาเลือกบัญชีธนาคาร', 'error')
                # Clean up uploaded file
                if os.path.exists(filepath):
                    os.remove(filepath)
                return redirect(request.url)

            # ตรวจสอบว่าบัญชีธนาคารที่เลือกอยู่ในบริษัทปัจจุบันหรือไม่
            bank_account = BankAccount.query.get(bank_account_id)
            if not bank_account or bank_account.company_id != company_id:
                flash('บัญชีธนาคารที่เลือกไม่ถูกต้องหรือไม่ได้อยู่ในบริษัทปัจจุบัน', 'error')
                if os.path.exists(filepath):
                    os.remove(filepath)
                return redirect(request.url)

            import_service = BankImportService(bank_type)

            try:
                print(f"Processing file: {file.filename}")
                transactions_data = import_service.parse_file(filepath)
                print(f"Successfully parsed {len(transactions_data)} transactions")

                # ตรวจสอบรายการซ้ำสำหรับแต่ละรายการ (แก้ให้ใช้ company_id)
                for item in transactions_data:
                    is_duplicate = check_duplicate_transaction(
                        current_user.id,
                        company_id,  # เพิ่ม company_id เพื่อตรวจสอบเฉพาะในบริษัทปัจจุบัน
                        item['date'],
                        item['amount'],
                        item['description']
                    )
                    item['is_duplicate'] = is_duplicate

                # บันทึกข้อมูลลงไฟล์ชั่วคราวแทนการเก็บใน session
                import_id = str(uuid.uuid4())
                temp_data_file = os.path.join(current_app.config['UPLOAD_FOLDER'], f"import_{import_id}.json")

                # Custom JSON serializer เพื่อจัดการกับ time objects
                def json_serializer(obj):
                    if hasattr(obj, 'isoformat'):  # สำหรับ date objects
                        return obj.isoformat()
                    elif hasattr(obj, 'strftime'):  # สำหรับ time objects
                        return obj.strftime('%H:%M:%S')
                    else:
                        return str(obj)

                with open(temp_data_file, 'w', encoding='utf-8') as f:
                    json.dump(transactions_data, f, default=json_serializer)

                session['import_id'] = import_id
                session['import_batch_id'] = str(uuid.uuid4())
                session['bank_type'] = bank_type
                session['bank_account_id'] = bank_account_id

                return redirect(url_for('imports.preview'))
            except Exception as e:
                import traceback
                print(f"Error parsing file: {str(e)}")
                print(traceback.format_exc())
                flash(f'เกิดข้อผิดพลาดในการอ่านไฟล์: {str(e)}', 'error')
                return redirect(request.url)
            finally:
                # Clean up uploaded file
                if os.path.exists(filepath):
                    os.remove(filepath)
        else:
            flash('รองรับเฉพาะไฟล์ Excel (.xlsx, .xls)', 'error')
            return redirect(request.url)

    # Get bank accounts for dropdown
    # ดึงบริษัทที่ active
    user_company = UserCompany.query.filter_by(
        user_id=current_user.id,
        active_company=True
    ).first()

    if not user_company:
        flash('ไม่พบข้อมูลบริษัทที่ใช้งานอยู่', 'error')
        return redirect(url_for('main.dashboard'))

    company_id = user_company.company_id

    # ดึงบัญชีธนาคารเฉพาะของบริษัทปัจจุบัน (ไม่ใช้ user_id)
    bank_accounts = BankAccount.query.filter_by(
        company_id=company_id,
        is_active=True
    ).all()

    return render_template('imports/upload.html', bank_accounts=bank_accounts)


# app/routes/imports.py - แก้ไขฟังก์ชัน preview() เพื่อจัดการ POST request

@imports_bp.route('/preview', methods=['GET', 'POST'])
@login_required
def preview():
    import_id = session.get('import_id')
    if not import_id:
        flash('ไม่พบข้อมูลการนำเข้า', 'error')
        return redirect(url_for('imports.upload'))

    # อ่านข้อมูลจากไฟล์ชั่วคราว
    temp_data_file = os.path.join(current_app.config['UPLOAD_FOLDER'], f"import_{import_id}.json")

    try:
        with open(temp_data_file, 'r', encoding='utf-8') as f:
            import_data = json.load(f)

        # แปลง string กลับเป็น datetime
        from datetime import datetime, time
        for item in import_data:
            if 'date' in item and isinstance(item['date'], str):
                item['date'] = datetime.strptime(item['date'], '%Y-%m-%d').date()
            # แปลงเวลาถ้ามี
            if 'time' in item and isinstance(item['time'], str):
                try:
                    # พยายามแปลงจาก string เป็น time object
                    time_parts = item['time'].split(':')
                    if len(time_parts) >= 2:
                        hour = int(time_parts[0])
                        minute = int(time_parts[1])
                        second = int(time_parts[2]) if len(time_parts) > 2 else 0
                        item['time'] = time(hour, minute, second)
                except Exception as e:
                    print(f"Error parsing time: {e}")
                    item['time'] = None

    except FileNotFoundError:
        flash('ไม่พบข้อมูลการนำเข้า', 'error')
        return redirect(url_for('imports.upload'))

    # POST processing - เพิ่มส่วนนี้
    if request.method == 'POST':
        # ดึงบริษัทที่ active
        user_company = UserCompany.query.filter_by(
            user_id=current_user.id,
            active_company=True
        ).first()

        if not user_company:
            flash('ไม่พบข้อมูลบริษัทที่ใช้งานอยู่', 'error')
            return redirect(url_for('main.dashboard'))

        company_id = user_company.company_id

        # ดึงข้อมูลจาก session
        batch_id = session.get('import_batch_id')
        bank_type = session.get('bank_type')
        bank_account_id = session.get('bank_account_id')
        original_filename = session.get('original_filename', 'unknown.xlsx')

        if not batch_id or not bank_type or not bank_account_id:
            flash('ข้อมูลการนำเข้าไม่ครบถ้วน กรุณาเริ่มใหม่', 'error')
            return redirect(url_for('imports.upload'))

        # ตรวจสอบบัญชีธนาคาร
        bank_account = BankAccount.query.get(bank_account_id)
        if not bank_account or bank_account.company_id != company_id:
            flash('บัญชีธนาคารไม่ถูกต้อง', 'error')
            return redirect(url_for('imports.upload'))

        # เริ่มการนำเข้าข้อมูล
        try:
            import_count = 0
            total_amount = 0

            for item in import_data:
                # ตรวจสอบว่ารายการนี้ถูกเลือกหรือไม่
                import_key = f"import_{item['index']}"

                # ถ้าเป็นรายการซ้ำ ต้องมีการเลือก import_duplicate
                if item.get('is_duplicate', False):
                    duplicate_key = f"import_duplicate_{item['index']}"
                    if duplicate_key not in request.form:
                        continue  # ข้ามรายการซ้ำที่ไม่ได้เลือก
                elif import_key not in request.form:
                    continue  # ข้ามรายการที่ไม่ได้เลือก

                # ดึงหมวดหมู่ที่เลือก
                category_key = f"category_{item['index']}"
                category_id = request.form.get(category_key)

                if not category_id:
                    continue  # ข้ามรายการที่ไม่มีหมวดหมู่

                # ตรวจสอบหมวดหมู่ว่าอยู่ในบริษัทปัจจุบันหรือไม่
                category = Category.query.get(category_id)
                if not category or category.company_id != company_id:
                    continue  # ข้ามรายการที่หมวดหมู่ไม่ถูกต้อง

                # สร้างธุรกรรมใหม่
                transaction = Transaction(
                    amount=item['amount'],
                    description=item.get('description', ''),
                    transaction_date=item['date'],
                    transaction_time=item.get('time'),
                    type=item['type'],
                    category_id=int(category_id),
                    bank_account_id=int(bank_account_id),
                    status='completed',  # รายการที่นำเข้าจากธนาคารจะเป็น completed
                    completed_date=datetime.now(bangkok_tz),
                    source='import',
                    bank_reference=item.get('reference', ''),
                    import_batch_id=batch_id,
                    user_id=current_user.id,
                    company_id=company_id
                )

                db.session.add(transaction)
                import_count += 1
                total_amount += item['amount']

            # สร้างประวัติการนำเข้า
            import_history = ImportHistory(
                batch_id=batch_id,
                filename=original_filename,
                bank_type=bank_type,
                transaction_count=import_count,
                total_amount=total_amount,
                status='completed',
                user_id=current_user.id,
                bank_account_id=int(bank_account_id),
                company_id=company_id
            )

            db.session.add(import_history)
            db.session.commit()

            # อัพเดทยอดเงินในบัญชี
            BalanceService.update_bank_balance(int(bank_account_id))

            # ล้างข้อมูลใน session
            session.pop('import_id', None)
            session.pop('import_batch_id', None)
            session.pop('bank_type', None)
            session.pop('bank_account_id', None)
            session.pop('original_filename', None)

            # ลบไฟล์ชั่วคราว
            try:
                if os.path.exists(temp_data_file):
                    os.remove(temp_data_file)
            except Exception as e:
                print(f"Error removing temp file: {e}")

            flash(f'นำเข้าข้อมูลสำเร็จ {import_count} รายการ ยอดรวม ฿{total_amount:,.2f}', 'success')
            return redirect(url_for('imports.history'))

        except Exception as e:
            db.session.rollback()
            print(f"Error importing transactions: {e}")
            import traceback
            print(traceback.format_exc())
            flash(f'เกิดข้อผิดพลาดในการนำเข้าข้อมูล: {str(e)}', 'error')
            return redirect(url_for('imports.upload'))

    # GET request - แสดงหน้า preview
    # ดึงบริษัทที่ active
    user_company = UserCompany.query.filter_by(
        user_id=current_user.id,
        active_company=True
    ).first()

    # ดึงหมวดหมู่ตามประเภทและตรวจสอบให้แน่ใจว่ามีหมวดหมู่
    income_categories = []
    expense_categories = []

    if user_company:
        # ดึงหมวดหมู่จากบริษัทปัจจุบัน แยกตามประเภท
        income_categories = Category.query.filter_by(
            company_id=user_company.company_id,
            type='income'
        ).all()

        expense_categories = Category.query.filter_by(
            company_id=user_company.company_id,
            type='expense'
        ).all()

    # ตรวจสอบว่ามีหมวดหมู่หรือไม่ ถ้าไม่มีให้สร้างใหม่
    if not income_categories and not expense_categories:
        from app.routes.auth import create_default_categories
        create_default_categories(current_user.id, user_company.company_id if user_company else None)

        # ดึงหมวดหมู่ใหม่อีกครั้ง
        if user_company:
            income_categories = Category.query.filter_by(
                company_id=user_company.company_id,
                type='income'
            ).all()

            expense_categories = Category.query.filter_by(
                company_id=user_company.company_id,
                type='expense'
            ).all()
        else:
            # ถ้าไม่มีบริษัทที่ active ให้ดึงโดยใช้แค่ user_id
            income_categories = Category.query.filter_by(
                user_id=current_user.id,
                type='income'
            ).all()

            expense_categories = Category.query.filter_by(
                user_id=current_user.id,
                type='expense'
            ).all()

    # รวมหมวดหมู่ทั้งหมด
    categories = income_categories + expense_categories

    print(f"Total categories: {len(categories)}")
    print(f"Income categories: {len(income_categories)}")
    print(f"Expense categories: {len(expense_categories)}")

    # Debug: แสดงรายละเอียดของรายการ
    for idx, item in enumerate(import_data[:3]):  # แสดงแค่ 3 รายการแรกเพื่อเช็ค
        print(f"Item {idx}: type={item.get('type')}, desc={item.get('description')[:20]}")

    matcher = CategoryMatcher(current_user.id)

    for item in import_data:
        # ตรวจสอบให้แน่ใจว่า type เป็น 'income' หรือ 'expense' เท่านั้น
        if item['type'] not in ['income', 'expense']:
            # แปลงเป็นรูปแบบที่ถูกต้อง
            item['type'] = 'income' if item['type'] == 'รายรับ' else 'expense'

        item['suggested_category_id'] = matcher.match_category(item['description'], item['type'])

        # แปลงเวลาเป็น string เพื่อแสดงใน template
        if 'time' in item and item['time']:
            if hasattr(item['time'], 'strftime'):
                item['time_display'] = item['time'].strftime('%H:%M:%S')
            else:
                item['time_display'] = str(item['time'])
        else:
            item['time_display'] = '-'

    return render_template('imports/preview.html',
                           import_data=import_data,
                           categories=categories)


@imports_bp.route('/history')
@login_required
def history():
    """แสดงประวัติการ import"""
    # ดึงบริษัทที่ active
    user_company = UserCompany.query.filter_by(
        user_id=current_user.id,
        active_company=True
    ).first()

    if not user_company:
        flash('ไม่พบข้อมูลบริษัทที่ใช้งานอยู่', 'error')
        return redirect(url_for('main.dashboard'))

    company_id = user_company.company_id

    # ดึงประวัติการนำเข้าเฉพาะในบริษัทปัจจุบัน
    import_histories = ImportHistory.query.filter_by(
        user_id=current_user.id,
        company_id=company_id
    ).order_by(ImportHistory.import_date.desc()).all()

    return render_template('imports/history.html', histories=import_histories)


@imports_bp.route('/delete/<string:batch_id>', methods=['POST'])
@login_required
def delete_import(batch_id):
    """ลบรายการที่ import โดยใช้ batch_id"""
    # ดึงบริษัทที่ active
    user_company = UserCompany.query.filter_by(
        user_id=current_user.id,
        active_company=True
    ).first()

    if not user_company:
        flash('ไม่พบข้อมูลบริษัทที่ใช้งานอยู่', 'error')
        return redirect(url_for('main.dashboard'))

    company_id = user_company.company_id

    # ต้องตรวจสอบทั้ง user_id และ company_id
    history = ImportHistory.query.filter_by(
        batch_id=batch_id,
        user_id=current_user.id,
        company_id=company_id
    ).first_or_404()

    bank_account_id = history.bank_account_id

    # ลบ transactions ที่เกี่ยวข้อง (ต้องตรวจสอบทั้ง user_id และ company_id)
    transactions = Transaction.query.filter_by(
        import_batch_id=batch_id,
        user_id=current_user.id,
        company_id=company_id
    ).all()

    for trans in transactions:
        db.session.delete(trans)

    # ลบประวัติ
    db.session.delete(history)
    db.session.commit()

    # อัพเดทยอดเงินในบัญชี
    if bank_account_id:
        BalanceService.update_bank_balance(bank_account_id)

    flash(f'ลบรายการนำเข้าจากไฟล์ {history.filename} เรียบร้อยแล้ว ({len(transactions)} รายการ)', 'success')
    return redirect(url_for('imports.history'))


# แก้ไขฟังก์ชัน check_duplicate_transaction ให้ตรวจสอบตาม company_id
def check_duplicate_transaction(user_id, company_id, date, amount, description):
    """ตรวจสอบว่ามีรายการซ้ำหรือไม่"""
    # ค้นหารายการที่มีวันที่, จำนวนเงิน และรายละเอียดเหมือนกัน
    # ตรวจสอบเฉพาะในบริษัทปัจจุบัน
    query = Transaction.query.filter_by(
        company_id=company_id,  # ใช้ company_id แทน user_id
        transaction_date=date,
        amount=amount
    )

    existing = query.all()

    # ตรวจสอบรายละเอียดเพิ่มเติม
    for trans in existing:
        if trans.description == description:
            return True

    return False