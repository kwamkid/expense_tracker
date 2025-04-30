# app/views/import_transactions.py
import os
import json
import uuid
import pickle
from datetime import datetime
from flask import Blueprint, render_template, redirect, url_for, flash, request, current_app, session
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.extensions import db
from app.forms.import_form import ImportForm, ImportConfirmForm
from app.models import Account, Category, Transaction
from app.models.category_matching import ImportBatch
from app.services.import_service import ImportService

imports_bp = Blueprint('imports', __name__, url_prefix='/imports')


# ฟังก์ชันใหม่สำหรับการจัดเก็บข้อมูลขนาดใหญ่ไว้ที่เซิร์ฟเวอร์แทนการใช้ session
def save_import_data_to_file(data, batch_reference):
    """
    บันทึกข้อมูลการนำเข้าลงไฟล์ชั่วคราวบนเซิร์ฟเวอร์แทนการใช้ session
    """
    # สร้างโฟลเดอร์สำหรับเก็บข้อมูลชั่วคราว (ถ้ายังไม่มี)
    temp_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'temp_imports')
    os.makedirs(temp_dir, exist_ok=True)

    # กำหนดชื่อไฟล์จาก batch_reference
    filename = os.path.join(temp_dir, f"{batch_reference}.pkl")

    # แปลงข้อมูล transaction ให้สามารถ serialize ได้
    serializable_data = data.copy()

    if 'transactions' in serializable_data:
        serializable_transactions = []
        for transaction in serializable_data['transactions']:
            t = transaction.copy()
            # แปลง datetime object เป็น string
            if isinstance(t.get('transaction_date'), datetime):
                t['transaction_date'] = t['transaction_date'].strftime('%Y-%m-%d')
            serializable_transactions.append(t)
        serializable_data['transactions'] = serializable_transactions

    # บันทึกข้อมูลลงไฟล์ด้วย pickle
    with open(filename, 'wb') as f:
        pickle.dump(serializable_data, f)

    return True


def load_import_data_from_file(batch_reference):
    """
    อ่านข้อมูลการนำเข้าจากไฟล์ชั่วคราวบนเซิร์ฟเวอร์
    """
    temp_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'temp_imports')
    filename = os.path.join(temp_dir, f"{batch_reference}.pkl")

    if not os.path.exists(filename):
        return None

    # อ่านข้อมูลจากไฟล์
    with open(filename, 'rb') as f:
        data = pickle.load(f)

    # แปลงข้อมูลกลับเป็น datetime object
    if 'transactions' in data:
        transactions = []
        for t in data['transactions']:
            transaction = t.copy()
            if isinstance(transaction.get('transaction_date'), str):
                transaction['transaction_date'] = datetime.strptime(transaction['transaction_date'], '%Y-%m-%d').date()
            transactions.append(transaction)
        data['transactions'] = transactions

    return data


def delete_import_data_file(batch_reference):
    """
    ลบไฟล์ข้อมูลชั่วคราวเมื่อเสร็จสิ้นหรือยกเลิกการนำเข้า
    """
    temp_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'temp_imports')
    filename = os.path.join(temp_dir, f"{batch_reference}.pkl")

    if os.path.exists(filename):
        os.remove(filename)
        return True
    return False


@imports_bp.route('/')
@login_required
def index():
    # แสดงประวัติการนำเข้า
    imports = ImportBatch.query.filter_by(
        organization_id=current_user.active_organization_id
    ).order_by(ImportBatch.created_at.desc()).all()

    return render_template(
        'imports/index.html',
        imports=imports,
        title='ประวัติการนำเข้าธุรกรรม'
    )


@imports_bp.route('/new', methods=['GET', 'POST'])
@login_required
def new():
    form = ImportForm()

    # ดึงบัญชีทั้งหมดของผู้ใช้สำหรับตัวเลือกในฟอร์ม
    form.account_id.choices = [(a.id, a.name) for a in Account.query.filter_by(
        organization_id=current_user.active_organization_id, is_active=True
    ).all()]

    if form.validate_on_submit():
        try:
            # บันทึกไฟล์ที่อัพโหลด
            file = form.file.data
            filename = secure_filename(file.filename)
            upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], 'imports')

            # สร้างโฟลเดอร์ถ้ายังไม่มี
            os.makedirs(upload_dir, exist_ok=True)

            # ชื่อไฟล์พร้อม timestamp เพื่อป้องกันชื่อซ้ำ
            timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
            file_path = os.path.join(upload_dir, f"{timestamp}_{filename}")
            file.save(file_path)

            # สร้าง imports batch
            import_batch = ImportService.create_import_batch(
                filename,
                form.bank.data.upper(),
                current_user.active_organization_id,
                current_user.id
            )

            # วิเคราะห์ไฟล์ Excel ตามธนาคารที่เลือก
            if form.bank.data == 'scb':
                result = ImportService.parse_scb_excel(
                    file_path,
                    current_user.active_organization_id
                )
            else:
                # สำหรับธนาคารอื่นๆ ในอนาคต
                result = {'success': False, 'error': 'ยังไม่รองรับธนาคารนี้'}

            if not result['success']:
                # ลบไฟล์ที่อัพโหลดกรณีเกิดข้อผิดพลาด
                if os.path.exists(file_path):
                    os.remove(file_path)

                # อัปเดตสถานะ batch เป็นล้มเหลว
                ImportService.update_batch_status(import_batch.batch_reference, 'failed')

                flash(f"เกิดข้อผิดพลาด: {result['error']}", 'danger')
                return redirect(url_for('imports.new'))

            # เก็บข้อมูลสำหรับหน้ายืนยันในไฟล์ชั่วคราวแทนการใช้ session
            import_data = {
                'file_path': file_path,
                'transactions': result['transactions'],
                'batch_reference': import_batch.batch_reference,
                'account_id': form.account_id.data
            }

            # บันทึกข้อมูลลงไฟล์
            save_import_data_to_file(import_data, import_batch.batch_reference)

            # เก็บเฉพาะ batch_reference ไว้ใน session เพื่อใช้อ้างอิงในหน้าถัดไป
            session['import_batch_reference'] = import_batch.batch_reference

            # อัปเดตจำนวนรายการใน batch
            ImportService.update_batch_status(
                import_batch.batch_reference,
                'processing',
                total_records=len(result['transactions'])
            )

            # ไปยังหน้ายืนยันการนำเข้า
            return redirect(url_for('imports.preview'))

        except Exception as e:
            current_app.logger.error(f"Error importing file: {str(e)}")
            flash(f"เกิดข้อผิดพลาดในการอัพโหลดไฟล์: {str(e)}", 'danger')

    return render_template(
        'imports/new.html',
        form=form,
        title='นำเข้าธุรกรรมใหม่'
    )


@imports_bp.route('/preview', methods=['GET', 'POST'])
@login_required
def preview():
    # ตรวจสอบว่ามี batch_reference ในเซสชัน
    if 'import_batch_reference' not in session:
        flash('ไม่พบข้อมูลการนำเข้า กรุณาเริ่มต้นใหม่', 'warning')
        return redirect(url_for('imports.new'))

    batch_reference = session['import_batch_reference']

    # ดึงข้อมูลจากไฟล์ชั่วคราว
    import_data = load_import_data_from_file(batch_reference)

    if not import_data:
        flash('ไม่พบข้อมูลการนำเข้า หรือข้อมูลอาจหมดอายุ กรุณาเริ่มต้นใหม่', 'warning')
        session.pop('import_batch_reference', None)
        return redirect(url_for('imports.new'))

    transactions = import_data['transactions']

    # สร้างฟอร์มสำหรับยืนยัน
    form = ImportConfirmForm()

    # ดึงบัญชีทั้งหมดของผู้ใช้สำหรับตัวเลือกในฟอร์ม
    all_accounts = Account.query.filter_by(
        organization_id=current_user.active_organization_id, is_active=True
    ).all()
    form.account_id.choices = [(a.id, a.name) for a in all_accounts]

    # ตั้งค่าเริ่มต้นจากข้อมูลที่เลือกในหน้าแรก
    form.account_id.data = import_data.get('account_id')

    # ดึงหมวดหมู่ทั้งหมดสำหรับแสดงในตัวเลือก
    income_categories = Category.query.filter_by(
        organization_id=current_user.active_organization_id, type='income'
    ).all()
    expense_categories = Category.query.filter_by(
        organization_id=current_user.active_organization_id, type='expense'
    ).all()

    # ตรวจสอบรายการที่อาจซ้ำซ้อน
    for transaction in transactions:
        # เช็คว่ามี hash ซ้ำหรือไม่
        duplicate = ImportService.check_duplicate_transaction(
            transaction['transaction_hash'],
            current_user.active_organization_id
        )
        transaction['is_duplicate'] = duplicate is not None

        # ถ้าไม่ซ้ำโดย hash ให้ตรวจสอบโดยวันที่และจำนวนเงิน
        if not transaction['is_duplicate']:
            potential_duplicates = ImportService.find_potential_duplicates(
                transaction['transaction_date'],
                transaction['amount'],
                current_user.active_organization_id,
                transaction['description']
            )
            transaction['potential_duplicates'] = len(potential_duplicates) > 0
        else:
            transaction['potential_duplicates'] = False

    if form.validate_on_submit():
        if 'cancel' in request.form:
            # ลบไฟล์ที่อัพโหลด
            if os.path.exists(import_data['file_path']):
                os.remove(import_data['file_path'])

            # อัปเดตสถานะ batch เป็นยกเลิก
            ImportService.update_batch_status(import_data['batch_reference'], 'cancelled')

            # ลบไฟล์ข้อมูลชั่วคราว
            delete_import_data_file(batch_reference)
            session.pop('import_batch_reference', None)

            flash('ยกเลิกการนำเข้าธุรกรรม', 'info')
            return redirect(url_for('imports.index'))

        try:
            # เตรียมข้อมูลธุรกรรมที่จะบันทึก
            transactions_to_save = []

            for i, transaction in enumerate(transactions):
                # ข้ามรายการที่เลือกไม่นำเข้า
                if f'import_{i}' not in request.form:
                    continue

                # ข้ามรายการซ้ำถ้าเลือกข้ามรายการซ้ำ
                if form.skip_duplicates.data and transaction['is_duplicate']:
                    continue

                # ใช้หมวดหมู่ที่ผู้ใช้เลือก
                category_id = int(request.form.get(f'category_{i}'))

                # ใช้บัญชีที่ผู้ใช้เลือกสำหรับรายการนี้ (ถ้ามีการเลือกแยก)
                account_id = int(request.form.get(f'account_id_{i}', form.account_id.data))

                # เพิ่มข้อมูลลงในรายการที่จะบันทึก
                transaction_data = transaction.copy()
                transaction_data['category_id'] = category_id
                transaction_data['selected_account_id'] = account_id
                transactions_to_save.append(transaction_data)

            # บันทึกรายการทั้งหมด (ปรับปรุงฟังก์ชันนี้เพื่อรองรับการบันทึกลงหลายบัญชี)
            result = ImportService.save_transactions_multi_accounts(
                transactions_to_save,
                import_data['batch_reference'],
                current_user.active_organization_id,
                current_user.id
            )

            # ลบไฟล์ที่อัพโหลด (เพราะข้อมูลถูกบันทึกลงฐานข้อมูลแล้ว)
            if os.path.exists(import_data['file_path']):
                os.remove(import_data['file_path'])

            # ลบไฟล์ข้อมูลชั่วคราว
            delete_import_data_file(batch_reference)
            session.pop('import_batch_reference', None)

            if result['success']:
                stats = result['stats']
                flash(
                    f"นำเข้าธุรกรรมสำเร็จ {stats['imported_records']} รายการ (ข้ามรายการซ้ำ {stats['duplicate_records']} รายการ, ผิดพลาด {stats['error_records']} รายการ)",
                    'success')
                return redirect(url_for('imports.index'))
            else:
                flash(f"เกิดข้อผิดพลาดในการบันทึกข้อมูล: {result['error']}", 'danger')

        except Exception as e:
            current_app.logger.error(f"Error saving transactions: {str(e)}")
            flash(f"เกิดข้อผิดพลาดในการนำเข้าข้อมูล: {str(e)}", 'danger')

    return render_template(
        'imports/preview.html',
        form=form,
        transactions=transactions,
        income_categories=income_categories,
        expense_categories=expense_categories,
        accounts=all_accounts,
        title='ตรวจสอบและยืนยันการนำเข้า'
    )


@imports_bp.route('/view/<batch_reference>')
@login_required
def view(batch_reference):
    # แสดงรายละเอียดการนำเข้า
    import_batch = ImportBatch.query.filter_by(
        batch_reference=batch_reference,
        organization_id=current_user.active_organization_id
    ).first_or_404()

    # ดึงรายการธุรกรรมที่นำเข้าในครั้งนี้
    transactions = import_batch.transactions

    return render_template(
        'imports/view.html',
        import_batch=import_batch,
        transactions=transactions,
        title=f'รายละเอียดการนำเข้า {import_batch.source}'
    )


@imports_bp.route('/delete/<batch_reference>', methods=['POST'])
@login_required
def delete(batch_reference):
    """ลบการนำเข้าทั้งชุดและย้อนคืนธุรกรรมทั้งหมดที่เกี่ยวข้อง"""
    import_batch = ImportBatch.query.filter_by(
        batch_reference=batch_reference,
        organization_id=current_user.active_organization_id
    ).first_or_404()

    # ตรวจสอบว่าสถานะเป็น completed หรือไม่ (จะลบได้เฉพาะการนำเข้าที่สำเร็จแล้ว)
    if import_batch.status != 'completed':
        flash('สามารถลบได้เฉพาะการนำเข้าที่สำเร็จแล้วเท่านั้น', 'warning')
        return redirect(url_for('imports.index'))

    try:
        # ดึงธุรกรรมทั้งหมดที่เกี่ยวข้องกับการนำเข้านี้
        transactions = Transaction.query.filter_by(
            import_batch_id=batch_reference,
            organization_id=current_user.active_organization_id
        ).all()

        # สร้าง dictionary เพื่อเก็บผลกระทบต่อยอดเงินในแต่ละบัญชี
        account_balances = {}

        # ประมวลผลทุกธุรกรรมและคำนวณยอดเงินที่ต้องเปลี่ยนแปลง
        for transaction in transactions:
            # ตรวจสอบเฉพาะธุรกรรมที่มีสถานะ 'completed'
            if transaction.status == 'completed':
                account_id = transaction.account_id
                if account_id not in account_balances:
                    account_balances[account_id] = 0

                # คำนวณยอดเงินที่ต้องย้อนคืน
                if transaction.type == 'income':
                    account_balances[account_id] -= transaction.amount
                else:
                    account_balances[account_id] += transaction.amount

        # อัปเดตยอดเงินในแต่ละบัญชี
        for account_id, balance_change in account_balances.items():
            account = Account.query.get(account_id)
            if account:
                account.balance += balance_change

        # ลบธุรกรรมทั้งหมด
        for transaction in transactions:
            # ลบไฟล์ใบเสร็จ (ถ้ามี) ที่เกี่ยวข้องกับธุรกรรมนี้
            if transaction.receipt_path:
                from app.services.file_service import delete_receipt
                delete_receipt(transaction.receipt_path)

            db.session.delete(transaction)

        # อัปเดตสถานะของการนำเข้าเป็น 'deleted'
        import_batch.status = 'deleted'

        # บันทึกการเปลี่ยนแปลงทั้งหมดลงฐานข้อมูล
        db.session.commit()

        flash(f'ลบการนำเข้าและธุรกรรมที่เกี่ยวข้องทั้งหมด {len(transactions)} รายการสำเร็จ', 'success')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Error deleting import: {str(e)}")
        flash(f'เกิดข้อผิดพลาดในการลบข้อมูล: {str(e)}', 'danger')

    return redirect(url_for('imports.index'))