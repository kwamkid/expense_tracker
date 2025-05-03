# app/routes/imports.py
from flask import Blueprint, render_template, request, redirect, url_for, flash, current_app, session
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app.models import db, Transaction, Category, ImportHistory
from app.services.import_service import BankImportService
from app.services.category_matcher import CategoryMatcher
import os
import uuid
import json
from datetime import datetime

imports_bp = Blueprint('imports', __name__, url_prefix='/imports')


@imports_bp.route('/upload', methods=['GET', 'POST'])
@login_required
def upload():
    if request.method == 'POST':
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
            file.save(filepath)

            # เก็บชื่อไฟล์ต้นฉบับไว้ใน session
            session['original_filename'] = file.filename

            # Process file
            bank_type = request.form.get('bank_type')
            import_service = BankImportService(bank_type)

            try:
                transactions_data = import_service.parse_file(filepath)

                # ตรวจสอบรายการซ้ำสำหรับแต่ละรายการ
                for item in transactions_data:
                    is_duplicate = check_duplicate_transaction(
                        current_user.id,
                        item['date'],
                        item['amount'],
                        item['description']
                    )
                    item['is_duplicate'] = is_duplicate

                # บันทึกข้อมูลลงไฟล์ชั่วคราวแทนการเก็บใน session
                import_id = str(uuid.uuid4())
                temp_data_file = os.path.join(current_app.config['UPLOAD_FOLDER'], f"import_{import_id}.json")

                with open(temp_data_file, 'w', encoding='utf-8') as f:
                    json.dump(transactions_data, f, default=str)  # default=str เพื่อจัดการกับ datetime

                session['import_id'] = import_id
                session['import_batch_id'] = str(uuid.uuid4())
                session['bank_type'] = bank_type

                return redirect(url_for('imports.preview'))
            except Exception as e:
                flash(f'เกิดข้อผิดพลาดในการอ่านไฟล์: {str(e)}', 'error')
                return redirect(request.url)
            finally:
                # Clean up uploaded file
                if os.path.exists(filepath):
                    os.remove(filepath)
        else:
            flash('รองรับเฉพาะไฟล์ Excel (.xlsx, .xls)', 'error')
            return redirect(request.url)

    return render_template('imports/upload.html')


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
        from datetime import datetime
        for item in import_data:
            if 'date' in item and isinstance(item['date'], str):
                item['date'] = datetime.strptime(item['date'], '%Y-%m-%d').date()

    except FileNotFoundError:
        flash('ไม่พบข้อมูลการนำเข้า', 'error')
        return redirect(url_for('imports.upload'))

    if request.method == 'POST':
        batch_id = session.get('import_batch_id')
        bank_type = session.get('bank_type')
        original_filename = session.get('original_filename', 'unknown')

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
                        type=item['type'],
                        name='อื่นๆ'
                    ).first()
                    category_id = category.id if category else None

                if category_id:
                    transaction = Transaction(
                        amount=item['amount'],
                        description=item['description'],
                        transaction_date=item['date'],
                        type=item['type'],
                        category_id=category_id,
                        user_id=current_user.id,
                        bank_reference=item.get('reference'),
                        import_batch_id=batch_id
                    )
                    db.session.add(transaction)
                    success_count += 1
                    total_amount += item['amount']
                else:
                    error_count += 1
            except Exception as e:
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
                user_id=current_user.id
            )
            db.session.add(import_history)

        db.session.commit()

        # Clean up
        if os.path.exists(temp_data_file):
            os.remove(temp_data_file)
        session.pop('import_id', None)
        session.pop('import_batch_id', None)
        session.pop('bank_type', None)
        session.pop('original_filename', None)

        # แสดงข้อความสรุป
        message = f'นำเข้าสำเร็จ {success_count} รายการ'
        if duplicate_count > 0:
            message += f', ข้ามรายการซ้ำ {duplicate_count} รายการ'
        if error_count > 0:
            message += f', ข้อผิดพลาด {error_count} รายการ'

        flash(message, 'success' if error_count == 0 else 'warning')
        return redirect(url_for('transactions.index'))

    # Prepare data for preview
    categories = Category.query.filter_by(user_id=current_user.id).all()
    matcher = CategoryMatcher(current_user.id)

    for item in import_data:
        item['suggested_category_id'] = matcher.match_category(item['description'], item['type'])

    return render_template('imports/preview.html',
                           import_data=import_data,
                           categories=categories)


@imports_bp.route('/history')
@login_required
def history():
    """แสดงประวัติการ import"""
    import_histories = ImportHistory.query.filter_by(user_id=current_user.id) \
        .order_by(ImportHistory.import_date.desc()).all()
    return render_template('imports/history.html', histories=import_histories)


@imports_bp.route('/delete/<string:batch_id>', methods=['POST'])
@login_required
def delete_import(batch_id):
    """ลบรายการที่ import โดยใช้ batch_id"""
    history = ImportHistory.query.filter_by(
        batch_id=batch_id,
        user_id=current_user.id
    ).first_or_404()

    # ลบ transactions ที่เกี่ยวข้อง
    transactions = Transaction.query.filter_by(
        import_batch_id=batch_id,
        user_id=current_user.id
    ).all()

    for trans in transactions:
        db.session.delete(trans)

    # ลบประวัติ
    db.session.delete(history)
    db.session.commit()

    flash(f'ลบรายการนำเข้าจากไฟล์ {history.filename} เรียบร้อยแล้ว ({len(transactions)} รายการ)', 'success')
    return redirect(url_for('imports.history'))


def allowed_file(filename):
    return '.' in filename and \
        filename.rsplit('.', 1)[1].lower() in {'xlsx', 'xls'}


def check_duplicate_transaction(user_id, date, amount, description):
    """ตรวจสอบว่ามีรายการซ้ำหรือไม่"""
    # ค้นหารายการที่มีวันที่, จำนวนเงิน และรายละเอียดเหมือนกัน
    existing = Transaction.query.filter_by(
        user_id=user_id,
        transaction_date=date,
        amount=amount
    ).all()

    # ตรวจสอบรายละเอียดเพิ่มเติม
    for trans in existing:
        if trans.description == description:
            return True

    return False