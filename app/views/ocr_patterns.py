# app/views/ocr_patterns.py
from flask import Blueprint, render_template, redirect, url_for, request, flash, jsonify
from flask_login import login_required, current_user
from app.models.ocr_pattern import OCRPattern
from app.extensions import db
import json
import re

ocr_patterns_bp = Blueprint('ocr_patterns', __name__, url_prefix='/ocr-patterns')


@ocr_patterns_bp.route('/')
@login_required
def index():
    """แสดงหน้าจัดการรูปแบบ OCR ทั้งหมด"""
    # รวบรวมข้อมูลเป็นกลุ่มตามชื่อ
    patterns_by_name = {}
    patterns = OCRPattern.query.order_by(OCRPattern.name, OCRPattern.priority.desc()).all()

    for pattern in patterns:
        if pattern.name not in patterns_by_name:
            patterns_by_name[pattern.name] = []
        patterns_by_name[pattern.name].append(pattern)

    # รวบรวมชื่อทั้งหมดเพื่อใช้ในการเพิ่มรูปแบบใหม่
    field_names = sorted(patterns_by_name.keys())
    if not field_names:
        field_names = ['date', 'total_amount', 'vendor', 'receipt_number', 'items_section']

    return render_template(
        'ocr_patterns/index.html',
        patterns_by_name=patterns_by_name,
        field_names=field_names,
        title='จัดการรูปแบบ OCR'
    )


@ocr_patterns_bp.route('/create', methods=['GET', 'POST'])
@login_required
def create():
    """เพิ่มรูปแบบ OCR ใหม่"""
    if request.method == 'POST':
        name = request.form.get('name')
        pattern = request.form.get('pattern')
        category = request.form.get('category', 'custom')
        description = request.form.get('description', '')
        example = request.form.get('example', '')
        priority = request.form.get('priority', 0)

        # ตรวจสอบข้อมูล
        if not name or not pattern:
            flash('กรุณากรอกชื่อและรูปแบบ regex', 'danger')
            return redirect(url_for('ocr_patterns.create'))

        # ตรวจสอบความถูกต้องของ regex
        try:
            re.compile(pattern)
        except re.error:
            flash('รูปแบบ regex ไม่ถูกต้อง', 'danger')
            return redirect(url_for('ocr_patterns.create'))

        # สร้างรูปแบบใหม่
        new_pattern = OCRPattern(
            name=name,
            pattern=pattern,
            category=category,
            description=description,
            example=example,
            priority=int(priority) if priority else 0,
            user_id=current_user.id
        )

        db.session.add(new_pattern)
        db.session.commit()

        flash('เพิ่มรูปแบบ OCR สำเร็จ!', 'success')
        return redirect(url_for('ocr_patterns.index'))

    # กรณี GET - แสดงฟอร์ม
    field_names = ['date', 'total_amount', 'vendor', 'receipt_number', 'items_section']
    categories = ['basic', 'thai', 'english', 'custom', 'receipt_specific']

    return render_template(
        'ocr_patterns/create.html',
        field_names=field_names,
        categories=categories,
        title='เพิ่มรูปแบบ OCR'
    )


@ocr_patterns_bp.route('/bulk-create', methods=['GET', 'POST'])
@login_required
def bulk_create():
    """เพิ่มรูปแบบ OCR หลายรายการพร้อมกัน"""
    if request.method == 'POST':
        field_name = request.form.get('field_name')
        if field_name == 'custom':
            field_name = request.form.get('custom_field_name')

        patterns_text = request.form.get('patterns')
        category = request.form.get('category', 'custom')
        base_priority = int(request.form.get('base_priority', 10))
        is_active = 'is_active' in request.form

        # ตรวจสอบข้อมูล
        if not field_name or not patterns_text:
            flash('กรุณากรอกชื่อฟิลด์และรูปแบบ regex', 'danger')
            return redirect(url_for('ocr_patterns.bulk_create'))

        # แยกรูปแบบแต่ละบรรทัด
        patterns = [p.strip() for p in patterns_text.strip().split('\n') if p.strip()]

        if not patterns:
            flash('ไม่พบรูปแบบ regex ที่ถูกต้อง', 'danger')
            return redirect(url_for('ocr_patterns.bulk_create'))

        # ตรวจสอบความถูกต้องของ regex แต่ละตัว
        invalid_patterns = []
        for pattern in patterns:
            try:
                re.compile(pattern)
            except re.error as e:
                invalid_patterns.append(f"{pattern}: {str(e)}")

        if invalid_patterns:
            flash(f'พบรูปแบบ regex ที่ไม่ถูกต้อง: {", ".join(invalid_patterns)}', 'danger')
            return redirect(url_for('ocr_patterns.bulk_create'))

        # เพิ่มรูปแบบทั้งหมด
        created_count = 0
        current_priority = base_priority

        for pattern in patterns:
            new_pattern = OCRPattern(
                name=field_name,
                pattern=pattern,
                category=category,
                description=f"รูปแบบสำหรับ {field_name} (เพิ่มแบบหลายรายการ)",
                example="",  # ไม่มีตัวอย่าง
                priority=current_priority,
                is_active=is_active,
                user_id=current_user.id
            )

            db.session.add(new_pattern)
            created_count += 1
            current_priority -= 1  # ลดลำดับความสำคัญลงสำหรับรูปแบบถัดไป

        db.session.commit()

        flash(f'เพิ่มรูปแบบ OCR สำเร็จ {created_count} รายการ!', 'success')
        return redirect(url_for('ocr_patterns.index'))

    # กรณี GET - แสดงฟอร์ม
    field_names = ['date', 'total_amount', 'vendor', 'receipt_number', 'items_section']
    categories = ['basic', 'thai', 'english', 'custom', 'receipt_specific']

    return render_template(
        'ocr_patterns/bulk_create.html',
        field_names=field_names,
        categories=categories,
        title='เพิ่มรูปแบบ OCR หลายรายการ'
    )


@ocr_patterns_bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    """แก้ไขรูปแบบ OCR"""
    pattern = OCRPattern.query.get_or_404(id)

    # ตรวจสอบสิทธิ์ (เฉพาะผู้ดูแลหรือเจ้าของเท่านั้น)
    if pattern.user_id is not None and pattern.user_id != current_user.id:
        flash('คุณไม่มีสิทธิ์แก้ไขรูปแบบนี้', 'danger')
        return redirect(url_for('ocr_patterns.index'))

    if request.method == 'POST':
        pattern.pattern = request.form.get('pattern')
        pattern.description = request.form.get('description', '')
        pattern.example = request.form.get('example', '')
        pattern.category = request.form.get('category', 'custom')
        pattern.priority = int(request.form.get('priority', 0))
        pattern.is_active = 'is_active' in request.form

        # ตรวจสอบความถูกต้องของ regex
        try:
            re.compile(pattern.pattern)
        except re.error:
            flash('รูปแบบ regex ไม่ถูกต้อง', 'danger')
            return redirect(url_for('ocr_patterns.edit', id=id))

        db.session.commit()
        flash('แก้ไขรูปแบบ OCR สำเร็จ!', 'success')
        return redirect(url_for('ocr_patterns.index'))

    # กรณี GET - แสดงฟอร์ม
    categories = ['basic', 'thai', 'english', 'custom', 'receipt_specific']

    return render_template(
        'ocr_patterns/edit.html',
        pattern=pattern,
        categories=categories,
        title='แก้ไขรูปแบบ OCR'
    )


@ocr_patterns_bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    """ลบรูปแบบ OCR"""
    pattern = OCRPattern.query.get_or_404(id)

    # ตรวจสอบสิทธิ์ (เฉพาะผู้ดูแลหรือเจ้าของเท่านั้น)
    if pattern.user_id is not None and pattern.user_id != current_user.id:
        flash('คุณไม่มีสิทธิ์ลบรูปแบบนี้', 'danger')
        return redirect(url_for('ocr_patterns.index'))

    db.session.delete(pattern)
    db.session.commit()

    flash('ลบรูปแบบ OCR สำเร็จ!', 'success')
    return redirect(url_for('ocr_patterns.index'))


@ocr_patterns_bp.route('/test', methods=['POST'])
@login_required
def test_pattern():
    """ทดสอบรูปแบบ regex กับข้อความ"""
    pattern = request.form.get('pattern', '')
    text = request.form.get('text', '')

    try:
        # คอมไพล์ regex
        regex = re.compile(pattern)

        # ค้นหาข้อความที่ตรงกับรูปแบบ
        matches = re.search(regex, text)

        if matches:
            # ดึงค่าจากกลุ่มที่ 1 (ส่วนที่ตรงกับ regex ในวงเล็บ)
            result = matches.group(1).strip()
            return jsonify({
                'success': True,
                'message': f'พบข้อความที่ตรงกับรูปแบบ: "{result}"',
                'result': result,
                'groups': [matches.group(i) for i in range(1, len(matches.groups()) + 1)]
            })
        else:
            return jsonify({
                'success': False,
                'message': 'ไม่พบข้อความที่ตรงกับรูปแบบ'
            })

    except re.error as e:
        return jsonify({
            'success': False,
            'message': f'รูปแบบ regex ไม่ถูกต้อง: {str(e)}'
        })
    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'เกิดข้อผิดพลาด: {str(e)}'
        })


@ocr_patterns_bp.route('/export', methods=['GET'])
@login_required
def export_patterns():
    """ส่งออกรูปแบบทั้งหมดเป็น JSON"""
    json_data = OCRPattern.export_to_json()
    return jsonify(json.loads(json_data))


@ocr_patterns_bp.route('/import', methods=['POST'])
@login_required
def import_patterns():
    """นำเข้ารูปแบบจาก JSON"""
    try:
        json_data = request.json

        if not json_data:
            return jsonify({
                'success': False,
                'message': 'ไม่พบข้อมูล JSON'
            }), 400

        # แปลงข้อมูลเป็น JSON string
        json_str = json.dumps(json_data)

        # นำเข้าข้อมูล
        OCRPattern.import_from_json(json_str)

        return jsonify({
            'success': True,
            'message': 'นำเข้ารูปแบบ OCR สำเร็จ!'
        })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': f'เกิดข้อผิดพลาด: {str(e)}'
        }), 400


@ocr_patterns_bp.route('/download-template', methods=['GET'])
def download_template():
    """ดาวน์โหลดเทมเพลต JSON สำหรับการนำเข้า"""
    template = {
        "date": [
            {
                "pattern": r"วันที่\s*(\d{1,2}/\d{1,2}/\d{4})",
                "category": "thai",
                "description": "รูปแบบวันที่ไทย: วันที่ DD/MM/YYYY",
                "example": "วันที่ 01/07/2019",
                "priority": 10
            },
            {
                "pattern": r"(\d{1,2}/\d{1,2}/\d{4})",
                "category": "basic",
                "description": "วันที่ทั่วไปรูปแบบ DD/MM/YYYY",
                "example": "01/07/2019",
                "priority": 5
            }
        ],
        "total_amount": [
            {
                "pattern": r"รวมทั้งสิ้น\s*(\d+(?:[.,]\d{1,2})?)",
                "category": "thai",
                "description": "จำนวนเงินรวมท้ายใบเสร็จ",
                "example": "รวมทั้งสิ้น 1,234.56",
                "priority": 10
            },
            {
                "pattern": r"TOTAL\s*(\d+(?:[.,]\d{1,2})?)",
                "category": "english",
                "description": "จำนวนเงินรวมภาษาอังกฤษ",
                "example": "TOTAL 1,234.56",
                "priority": 5
            }
        ],
        "vendor": [
            {
                "pattern": r"^(บริษัท.+?)[\r\n]",
                "category": "thai",
                "description": "ชื่อบริษัทบรรทัดแรก",
                "example": "บริษัทโฟลร์แอคเคาหท์ จํากัด",
                "priority": 10
            }
        ],
        "receipt_number": [
            {
                "pattern": r"เลขที่\s*([A-Za-z0-9\-_/]+)",
                "category": "thai",
                "description": "เลขที่ใบเสร็จภาษาไทย",
                "example": "เลขที่ INV-2023-001",
                "priority": 10
            },
            {
                "pattern": r"(?:No|NO|no)\.?\s*([A-Za-z0-9\-_/]+)",
                "category": "english",
                "description": "เลขที่ใบเสร็จภาษาอังกฤษ",
                "example": "No. INV-2023-001",
                "priority": 5
            }
        ],
        "items_section": [
            {
                "pattern": r"(?:รายการ|สินค้า):(.*?)(?:รวมเป็นเงิน|รวมทั้งสิ้น)",
                "category": "thai",
                "description": "ส่วนรายการสินค้าภาษาไทย",
                "example": "รายการ: สินค้า A 100.00 สินค้า B 200.00 รวมเป็นเงิน",
                "priority": 10
            }
        ]
    }

    return jsonify(template)


@ocr_patterns_bp.route('/seed-default-patterns', methods=['POST'])
@login_required
def seed_default_patterns():
    """เพิ่มรูปแบบ OCR พื้นฐาน"""
    # ตรวจสอบว่ามีรูปแบบในฐานข้อมูลหรือไม่
    existing_count = OCRPattern.query.count()

    if existing_count > 0:
        flash('มีรูปแบบ OCR ในระบบอยู่แล้ว ไม่สามารถเพิ่มรูปแบบพื้นฐานได้', 'warning')
        return redirect(url_for('ocr_patterns.index'))

    # สร้างรูปแบบพื้นฐาน
    default_patterns = [
        # วันที่
        OCRPattern(
            name='date',
            pattern=r'วันที่\s*(\d{1,2}/\d{1,2}/\d{4})',
            category='thai',
            description='รูปแบบวันที่ไทย: วันที่ DD/MM/YYYY',
            example='วันที่ 01/07/2019',
            priority=10
        ),
        OCRPattern(
            name='date',
            pattern=r'(\d{1,2}/\d{1,2}/\d{4})',
            category='basic',
            description='วันที่ทั่วไปรูปแบบ DD/MM/YYYY',
            example='01/07/2019',
            priority=5
        ),
        OCRPattern(
            name='date',
            pattern=r'(?:Date|DATE):?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',
            category='english',
            description='วันที่ภาษาอังกฤษ',
            example='Date: 01/07/2019',
            priority=3
        ),

        # จำนวนเงินรวม
        OCRPattern(
            name='total_amount',
            pattern=r'รวมทั้งสิ้น\s*(\d+(?:[.,]\d{1,2})?)',
            category='thai',
            description='จำนวนเงินรวมท้ายใบเสร็จ',
            example='รวมทั้งสิ้น 1,234.56',
            priority=10
        ),
        OCRPattern(
            name='total_amount',
            pattern=r'จำนวนเงินหลังหักส่วนลด\s*(\d+(?:[.,]\d{1,2})?)',
            category='thai',
            description='จำนวนเงินหลังหักส่วนลด',
            example='จำนวนเงินหลังหักส่วนลด 1,234.56',
            priority=9
        ),
        OCRPattern(
            name='total_amount',
            pattern=r'TOTAL\s*(\d+(?:[.,]\d{1,2})?)',
            category='english',
            description='จำนวนเงินรวมภาษาอังกฤษ',
            example='TOTAL 1,234.56',
            priority=5
        ),

        # ชื่อร้านค้า
        OCRPattern(
            name='vendor',
            pattern=r'^(บริษัท.+?)[\r\n]',
            category='thai',
            description='ชื่อบริษัทบรรทัดแรก',
            example='บริษัทโฟลร์แอคเคาหท์ จํากัด',
            priority=10
        ),
        OCRPattern(
            name='vendor',
            pattern=r'^(ร้าน.+?)[\r\n]',
            category='thai',
            description='ชื่อร้านค้าบรรทัดแรก',
            example='ร้านขายของชำ',
            priority=8
        ),

        # เลขที่ใบเสร็จ
        OCRPattern(
            name='receipt_number',
            pattern=r'เลขที่\s*([A-Za-z0-9\-_/]+)',
            category='thai',
            description='เลขที่ใบเสร็จภาษาไทย',
            example='เลขที่ INV-2023-001',
            priority=10
        ),
        OCRPattern(
            name='receipt_number',
            pattern=r'(?:ใบกำกับภาษี|ใบเสร็จรับเงิน).*?(?:เลขที่)\s*([A-Za-z0-9\-_/]+)',
            category='thai',
            description='เลขที่ใบกำกับภาษี/ใบเสร็จรับเงิน',
            example='ใบกำกับภาษี เลขที่ T-2023001',
            priority=8
        ),
        OCRPattern(
            name='receipt_number',
            pattern=r'(?:No|NO|no)\.?\s*([A-Za-z0-9\-_/]+)',
            category='english',
            description='เลขที่ใบเสร็จภาษาอังกฤษ',
            example='No. INV-2023-001',
            priority=5
        ),

        # เพิ่ม regex ใหม่สำหรับใบเสร็จ FlowAccount
        OCRPattern(
            name='total_amount',
            pattern=r'รวมทั้งสิน\s*(\d{1,3}(?:,\d{3})*\.\d{2})',
            category='thai',
            description='รูปแบบรวมทั้งสิน (Flow Account)',
            example='รวมทั้งสิน 10,000.00',
            priority=15
        ),
        OCRPattern(
            name='total_amount',
            pattern=r'รวมทั้งสิน\s*"?(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)"?',
            category='thai',
            description='รูปแบบรวมทั้งสินอีกแบบ (Flow Account)',
            example='รวมทั้งสิน "10,000"',
            priority=14
        ),
        OCRPattern(
            name='receipt_number',
            pattern=r'([A-Z]{2}\d{10}(?:\.\d+)?)',
            category='thai',
            description='เลขที่ใบเสร็จ Flow Account',
            example='CA2019070001',
            priority=12
        ),
        OCRPattern(
            name='vendor',
            pattern=r'^(บริษัท.*?จํากัด)',
            category='thai',
            description='ชื่อบริษัทพร้อมคำว่าจำกัด',
            example='บริษัท โฟลว์แอคเค้าที่ จํากัด',
            priority=15
        ),
        OCRPattern(
            name='vendor',
            pattern=r'(บริษัท.*?จํากัด.*?)[\n\r]',
            category='thai',
            description='ชื่อบริษัทพร้อมคำว่าจำกัดและข้อมูลเพิ่มเติม',
            example='บริษัท โฟลว์แอคเค้าที่ จํากัด (สํานักงานใหญ่)',
            priority=14
        ),
    ]

    for pattern in default_patterns:
        db.session.add(pattern)

    db.session.commit()

    flash('เพิ่มรูปแบบ OCR พื้นฐานสำเร็จ!', 'success')
    return redirect(url_for('ocr_patterns.index'))