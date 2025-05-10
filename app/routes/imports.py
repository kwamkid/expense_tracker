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

    if request.method == 'POST':
        batch_id = session.get('import_batch_id')
        bank_type = session.get('bank_type')
        bank_account_id = session.get('bank_account_id')
        original_filename = session.get('original_filename', 'unknown')

        # ดึงบริษัทที่ active จาก UserCompany
        user_company = UserCompany.query.filter_by(
            user_id=current_user.id,
            active_company=True
        ).first()

        if not user_company:
            flash('ไม่พบข้อมูลบริษัทที่ใช้งานอยู่', 'error')
            return redirect(url_for('main.dashboard'))

        company_id = user_company.company_id

        matcher = CategoryMatcher(current_user.id)

        success_count = 0
        error_count = 0
        duplicate_count = 0
        total_amount = 0

        for item in import_data:
            # Skip if user unchecked this item
            if not request.form.get(f'import_{item["index"]}'):
                continue

            # ตรวจสอบว่าเป็นรายการซ้ำและผู้ใช้เลือกที่จะไม่นำเข้า
            if item.get('is_duplicate') and not request.form.get(f'import_duplicate_{item["index"]}'):
                duplicate_count += 1
                continue

            try:
                # Get selected category or auto-match
                category_id = request.form.get(f'category_{item["index"]}')
                if not category_id:
                    category_id = matcher.match_category(item['description'], item['type'])

                if not category_id:
                    # Use default "Other" category
                    category = Category.query.filter_by(
                        user_id=current_user.id,
                        company_id=company_id,  # เพิ่มบรรทัดนี้เพื่อให้ค้นหาเฉพาะหมวดหมู่ในบริษัทปัจจุบัน
                        type=item['type'],
                        name='อื่นๆ'
                    ).first()
                    category_id = category.id if category else None

                if category_id:
                    transaction = Transaction(
                        amount=item['amount'],
                        description=item['description'],
                        transaction_date=item['date'],
                        transaction_time=item.get('time'),  # เพิ่มเวลา
                        type=item['type'],
                        category_id=category_id,
                        user_id=current_user.id,
                        bank_reference=item.get('reference'),
                        import_batch_id=batch_id,
                        bank_account_id=bank_account_id,
                        status='completed',  # รายการที่ import มาต้องเป็น completed
                        source='import',
                        completed_date=datetime.now(bangkok_tz),
                        company_id=company_id  # ใช้ company_id จาก active company
                    )
                    db.session.add(transaction)
                    success_count += 1
                    total_amount += item['amount']
                else:
                    error_count += 1
            except Exception as e:
                print(f"Error creating transaction: {e}")
                error_count += 1

        # บันทึกประวัติการ import
        if success_count > 0:
            import_history = ImportHistory(
                batch_id=batch_id,
                filename=original_filename,
                bank_type=bank_type,
                transaction_count=success_count,
                total_amount=total_amount,
                status='completed' if error_count == 0 else 'partial',
                user_id=current_user.id,
                bank_account_id=bank_account_id,
                company_id=company_id  # ใช้ company_id จาก active company
            )
            db.session.add(import_history)

        try:
            db.session.commit()
            print(f"Successfully committed {success_count} transactions")
        except Exception as e:
            db.session.rollback()
            print(f"Error during commit: {e}")
            flash(f'เกิดข้อผิดพลาดในการบันทึกข้อมูล: {str(e)}', 'error')
            return redirect(url_for('transactions.index'))

        # อัพเดทยอดเงินในบัญชี
        if success_count > 0:
            try:
                BalanceService.update_bank_balance(bank_account_id)
            except Exception as e:
                print(f"Error updating bank balance: {e}")

        # Clean up
        if os.path.exists(temp_data_file):
            os.remove(temp_data_file)
        session.pop('import_id', None)
        session.pop('import_batch_id', None)
        session.pop('bank_type', None)
        session.pop('bank_account_id', None)
        session.pop('original_filename', None)

        # แสดงข้อความสรุป
        message = f'นำเข้าสำเร็จ {success_count} รายการ'
        if duplicate_count > 0:
            message += f', ข้ามรายการซ้ำ {duplicate_count} รายการ'
        if error_count > 0:
            message += f', ข้อผิดพลาด {error_count} รายการ'

        flash(message, 'success' if error_count == 0 else 'warning')
        return redirect(url_for('transactions.index'))

    # Prepare data for preview - เพิ่มการแสดงเวลาด้วย
    # ดึงบริษัทที่ active
    user_company = UserCompany.query.filter_by(
        user_id=current_user.id,
        active_company=True
    ).first()

    if user_company:
        # ดึงหมวดหมู่จากบริษัทปัจจุบัน
        categories = Category.query.filter_by(
            user_id=current_user.id,
            company_id=user_company.company_id
        ).all()
    else:
        # ถ้าไม่มีบริษัทที่ active ให้ดึงโดยใช้แค่ user_id
        categories = Category.query.filter_by(user_id=current_user.id).all()

    matcher = CategoryMatcher(current_user.id)

    for item in import_data:
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