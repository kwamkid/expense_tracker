# app/routes/auth.py
from flask import Blueprint, redirect, url_for, request, session, flash
from flask_login import login_user, logout_user, login_required
from app.models import db, User, Category, BankAccount
from app.services.line_auth import LineAuth
import uuid

auth_bp = Blueprint('auth', __name__, url_prefix='/auth')


@auth_bp.route('/login')
def login():
    try:
        state = str(uuid.uuid4())
        session['oauth_state'] = state

        # Check for invite token
        invite_token = request.args.get('invite')
        if invite_token:
            session['invite_token'] = invite_token

        line_auth = LineAuth()
        login_url = line_auth.get_login_url(state)
        return redirect(login_url)
    except ValueError as e:
        flash(str(e), 'error')
        return redirect(url_for('main.index'))
    except Exception as e:
        flash('เกิดข้อผิดพลาดในการเข้าสู่ระบบ กรุณาตรวจสอบการตั้งค่า LINE Login', 'error')
        return redirect(url_for('main.index'))


# แก้ไขฟังก์ชัน callback เพื่อรองรับการเชิญที่ดีขึ้น
@auth_bp.route('/callback')
def callback():
    code = request.args.get('code')
    state = request.args.get('state')

    if state != session.get('oauth_state'):
        flash('Invalid state parameter', 'error')
        return redirect(url_for('auth.login'))

    try:
        line_auth = LineAuth()
        token_data = line_auth.get_access_token(code)

        if 'access_token' not in token_data:
            flash('Failed to get access token', 'error')
            return redirect(url_for('auth.login'))

        profile = line_auth.get_user_profile(token_data['access_token'])

        # ตรวจสอบ invite token
        invite_token = session.pop('invite_token', None)

        # Find or create user
        user = User.query.filter_by(line_id=profile['userId']).first()
        is_new_user = False

        if not user:
            is_new_user = True
            user = User(
                line_id=profile['userId'],
                name=profile.get('displayName'),
                picture_url=profile.get('pictureUrl')
            )
            db.session.add(user)
            db.session.commit()

            # ถ้าไม่ได้รับเชิญให้สร้างบริษัทใหม่
            if not invite_token:
                company = Company(
                    name=f"บริษัทของ {user.name or 'ผู้ใช้ใหม่'}",
                    created_at=datetime.now(bangkok_tz),
                    owner_id=user.id
                )
                db.session.add(company)
                db.session.commit()

                # เชื่อมโยงผู้ใช้กับบริษัท
                user.company_id = company.id
                db.session.commit()

                # Create default categories for new user
                create_default_categories(user.id, company.id)

                # Create default bank account for new user
                create_default_bank_account(user.id, company.id)

        login_user(user)

        # Handle invite token
        if invite_token:
            process_invite_token(invite_token, user.id, is_new_user)

        return redirect(url_for('main.dashboard'))
    except Exception as e:
        flash(f'เกิดข้อผิดพลาดในการเข้าสู่ระบบ: {str(e)}', 'error')
        return redirect(url_for('main.index'))


# แก้ไขฟังก์ชัน create_default_categories และ create_default_bank_account เพื่อรองรับ company_id
def create_default_categories(user_id, company_id=None):
    default_categories = [
        # รายรับ
        {'name': 'ค่าคอร์ส', 'type': 'income', 'keywords': 'ค่าคอร์ส,course,คอร์สเรียน'},
        {'name': 'ค่าสอนพิเศษตามโรงเรียน', 'type': 'income', 'keywords': 'สอนพิเศษ,โรงเรียน,tutor,school'},
        {'name': 'ค่าสอนพิเศษตามบ้าน', 'type': 'income', 'keywords': 'สอนพิเศษ,ตามบ้าน,บ้าน,home tutor'},
        {'name': 'ขายสินค้า', 'type': 'income', 'keywords': 'ขาย,สินค้า,sale,product'},
        {'name': 'ค่าสมัครสมาชิก', 'type': 'income', 'keywords': 'สมัคร,สมาชิก,membership,registration'},
        {'name': 'ค่าหนังสือ/เอกสาร', 'type': 'income', 'keywords': 'หนังสือ,เอกสาร,book,document'},
        {'name': 'ค่าสอบ/ทดสอบ', 'type': 'income', 'keywords': 'สอบ,ทดสอบ,exam,test'},

        # รายจ่าย
        {'name': 'ค่าก่อสร้าง/เฟอร์นิเจอร์', 'type': 'expense',
         'keywords': 'ก่อสร้าง,เฟอร์นิเจอร์,construction,furniture'},
        {'name': 'ค่าอาหาร', 'type': 'expense', 'keywords': 'อาหาร,food,restaurant,ร้านอาหาร'},
        {'name': 'ค่าสาธารณูปโภค', 'type': 'expense',
         'keywords': 'ค่าเช่า,ค่าน้ำ,ค่าไฟ,utilities,rent,water,electricity'},
        {'name': 'ค่าอุปกรณ์การสอน', 'type': 'expense', 'keywords': 'อุปกรณ์,การสอน,teaching,materials,stationery'},
        {'name': 'ค่าเงินเดือน', 'type': 'expense', 'keywords': 'เงินเดือน,salary,wage,พนักงาน'},
        {'name': 'ค่าการตลาด/โฆษณา', 'type': 'expense', 'keywords': 'การตลาด,โฆษณา,marketing,advertising'},
        {'name': 'ค่าซ่อมบำรุง', 'type': 'expense', 'keywords': 'ซ่อม,บำรุง,maintenance,repair'},
        {'name': 'ค่าใช้จ่ายสำนักงาน', 'type': 'expense', 'keywords': 'สำนักงาน,office,supplies'},
        {'name': 'ค่าพัฒนาระบบ/IT', 'type': 'expense', 'keywords': 'คอมพิวเตอร์,IT,software,hardware'},

        # อื่นๆ
        {'name': 'อื่นๆ', 'type': 'income', 'keywords': ''},
        {'name': 'อื่นๆ', 'type': 'expense', 'keywords': ''}
    ]

    for cat in default_categories:
        category = Category(
            name=cat['name'],
            type=cat['type'],
            keywords=cat['keywords'],
            user_id=user_id,
            company_id=company_id  # เพิ่มความสัมพันธ์กับบริษัท
        )
        db.session.add(category)

    db.session.commit()


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))


def create_default_categories(user_id):
    default_categories = [
        # รายรับ
        {'name': 'ค่าคอร์ส', 'type': 'income', 'keywords': 'ค่าคอร์ส,course,คอร์สเรียน'},
        {'name': 'ค่าสอนพิเศษตามโรงเรียน', 'type': 'income', 'keywords': 'สอนพิเศษ,โรงเรียน,tutor,school'},
        {'name': 'ค่าสอนพิเศษตามบ้าน', 'type': 'income', 'keywords': 'สอนพิเศษ,ตามบ้าน,บ้าน,home tutor'},
        {'name': 'ขายสินค้า', 'type': 'income', 'keywords': 'ขาย,สินค้า,sale,product'},
        {'name': 'ค่าสมัครสมาชิก', 'type': 'income', 'keywords': 'สมัคร,สมาชิก,membership,registration'},
        {'name': 'ค่าหนังสือ/เอกสาร', 'type': 'income', 'keywords': 'หนังสือ,เอกสาร,book,document'},
        {'name': 'ค่าสอบ/ทดสอบ', 'type': 'income', 'keywords': 'สอบ,ทดสอบ,exam,test'},

        # รายจ่าย
        {'name': 'ค่าก่อสร้าง/เฟอร์นิเจอร์', 'type': 'expense',
         'keywords': 'ก่อสร้าง,เฟอร์นิเจอร์,construction,furniture'},
        {'name': 'ค่าอาหาร', 'type': 'expense', 'keywords': 'อาหาร,food,restaurant,ร้านอาหาร'},
        {'name': 'ค่าสาธารณูปโภค', 'type': 'expense',
         'keywords': 'ค่าเช่า,ค่าน้ำ,ค่าไฟ,utilities,rent,water,electricity'},
        {'name': 'ค่าอุปกรณ์การสอน', 'type': 'expense', 'keywords': 'อุปกรณ์,การสอน,teaching,materials,stationery'},
        {'name': 'ค่าเงินเดือน', 'type': 'expense', 'keywords': 'เงินเดือน,salary,wage,พนักงาน'},
        {'name': 'ค่าการตลาด/โฆษณา', 'type': 'expense', 'keywords': 'การตลาด,โฆษณา,marketing,advertising'},
        {'name': 'ค่าซ่อมบำรุง', 'type': 'expense', 'keywords': 'ซ่อม,บำรุง,maintenance,repair'},
        {'name': 'ค่าใช้จ่ายสำนักงาน', 'type': 'expense', 'keywords': 'สำนักงาน,office,supplies'},
        {'name': 'ค่าพัฒนาระบบ/IT', 'type': 'expense', 'keywords': 'คอมพิวเตอร์,IT,software,hardware'},

        # อื่นๆ
        {'name': 'อื่นๆ', 'type': 'income', 'keywords': ''},
        {'name': 'อื่นๆ', 'type': 'expense', 'keywords': ''}
    ]

    for cat in default_categories:
        category = Category(
            name=cat['name'],
            type=cat['type'],
            keywords=cat['keywords'],
            user_id=user_id
        )
        db.session.add(category)

    db.session.commit()


def create_default_bank_account(user_id, company_id=None):
    """สร้างบัญชีธนาคาร default สำหรับผู้ใช้ใหม่"""
    default_account = BankAccount(
        bank_name='ธนาคารหลัก',
        account_number='XXXX',
        account_name='บัญชีหลัก',
        initial_balance=0,
        current_balance=0,
        is_active=True,
        user_id=user_id,
        company_id=company_id  # เพิ่มความสัมพันธ์กับบริษัท
    )
    db.session.add(default_account)
    db.session.commit()


def process_invite_token(token, user_id, is_new_user=False):
    """จัดการ invite token และเชื่อมโยงผู้ใช้กับบริษัท"""
    from app.models import InviteToken, User, Company, Category, BankAccount, db

    invite = InviteToken.query.filter_by(token=token, used=False).first()
    if invite:
        # อัปเดตสถานะของคำเชิญเป็นใช้แล้ว
        invite.used = True
        invite.used_by = user_id

        # ถ้ามีการเชื่อมโยงกับบริษัท
        if invite.company_id:
            user = User.query.get(user_id)
            if user:
                # เชื่อมโยงผู้ใช้กับบริษัทของผู้เชิญ
                user.company_id = invite.company_id

                # ตรวจสอบว่ามีบริษัทส่วนตัวอยู่ก่อนหรือไม่
                old_company = Company.query.filter_by(owner_id=user.id).first()
                if old_company and old_company.id != invite.company_id:
                    # ถ้ามีบริษัทส่วนตัวอยู่แล้ว ให้ย้ายหมวดหมู่และบัญชีธนาคารมาที่บริษัทใหม่
                    Category.query.filter_by(company_id=old_company.id).update({'company_id': invite.company_id})
                    BankAccount.query.filter_by(company_id=old_company.id).update({'company_id': invite.company_id})

                    # ลบบริษัทเก่า
                    db.session.delete(old_company)

        db.session.commit()

        return True
    return False