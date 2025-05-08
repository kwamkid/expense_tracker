# app/routes/auth.py
from flask import Blueprint, redirect, url_for, request, session, flash, render_template
from flask_login import login_user, logout_user, login_required, current_user
from app.models import db, User, Category, BankAccount, Company, InviteToken, UserCompany
from app.services.line_auth import LineAuth
import uuid
from datetime import datetime
import pytz

bangkok_tz = pytz.timezone('Asia/Bangkok')

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

        login_user(user)

        # Handle invite token (เข้าร่วมบริษัทจากลิงก์เชิญ)
        if invite_token:
            if process_invite_token(invite_token, user.id, is_new_user):
                # แม้จะมีการเชิญและเข้าร่วมสำเร็จ ก็ยังบังคับให้ไปที่หน้าเลือกบริษัท
                flash('คุณได้เข้าร่วมบริษัทเรียบร้อยแล้ว กรุณาเลือกบริษัทที่ต้องการใช้งาน', 'success')
                return redirect(url_for('auth.select_company'))

        # ปรับให้ทุกบริษัทไม่ active ก่อน เพื่อบังคับให้ต้องเลือกบริษัท
        UserCompany.query.filter_by(user_id=user.id).update({'active_company': False})
        db.session.commit()

        # ตรวจสอบว่าผู้ใช้มีบริษัทหรือไม่
        user_companies = UserCompany.query.filter_by(user_id=user.id).all()

        # ถ้าผู้ใช้ไม่มีบริษัทเลย
        if not user_companies:
            flash('กรุณาสร้างบริษัทใหม่', 'info')
            return redirect(url_for('auth.select_company'))

        # บังคับให้ไปที่หน้าเลือกบริษัทเสมอ (แม้จะมีเพียงบริษัทเดียว)
        flash('กรุณาเลือกบริษัทที่ต้องการใช้งาน', 'info')
        return redirect(url_for('auth.select_company'))

    except Exception as e:
        flash(f'เกิดข้อผิดพลาดในการเข้าสู่ระบบ: {str(e)}', 'error')
        return redirect(url_for('main.index'))


@auth_bp.route('/select_company', methods=['GET', 'POST'])
@login_required
def select_company():
    # ตรวจสอบว่าผู้ใช้มี company_id แต่ไม่มีข้อมูลใน UserCompany หรือไม่
    if current_user.company_id:
        existing_relation = UserCompany.query.filter_by(
            user_id=current_user.id,
            company_id=current_user.company_id
        ).first()

        # ถ้าไม่มีความสัมพันธ์ แต่มี company_id ให้สร้างความสัมพันธ์ใหม่
        if not existing_relation:
            # ดึงข้อมูลบริษัท
            company = Company.query.get(current_user.company_id)
            if company:
                # สร้างความสัมพันธ์ใหม่
                user_company = UserCompany(
                    user_id=current_user.id,
                    company_id=current_user.company_id,
                    is_admin=(company.owner_id == current_user.id),  # ถ้าเป็นเจ้าของบริษัทให้เป็นแอดมิน
                    active_company=False  # ตั้งเป็น False เพื่อบังคับให้ต้องเลือก
                )
                db.session.add(user_company)
                db.session.commit()
                print(f"Created relationship for user {current_user.id} and company {current_user.company_id}")

    # ดึงบริษัทที่ผู้ใช้เป็นสมาชิก
    user_companies = UserCompany.query.filter_by(user_id=current_user.id).all()

    # พิมพ์ข้อมูลสำหรับ debug
    print(f"User {current_user.id} ({current_user.name}) has {len(user_companies)} companies")
    for uc in user_companies:
        print(f"Company ID: {uc.company_id}, Name: {uc.company.name}, Is Admin: {uc.is_admin}")

    if request.method == 'POST':
        if 'company_id' in request.form:
            # เลือกบริษัทที่มีอยู่
            company_id = request.form.get('company_id')

            # ปรับให้ทุกบริษัทไม่ active ก่อน
            UserCompany.query.filter_by(user_id=current_user.id).update({'active_company': False})

            # ตั้งค่าบริษัทที่เลือกเป็น active
            user_company = UserCompany.query.filter_by(
                user_id=current_user.id,
                company_id=company_id
            ).first_or_404()
            user_company.active_company = True
            db.session.commit()

            flash(f'เลือกบริษัท {user_company.company.name} เรียบร้อยแล้ว', 'success')
            return redirect(url_for('main.dashboard'))

        elif 'new_company_name' in request.form:
            # สร้างบริษัทใหม่
            company_name = request.form.get('new_company_name')

            # ตรวจสอบชื่อบริษัท
            if not company_name or len(company_name.strip()) < 3:
                flash('ชื่อบริษัทต้องมีความยาวอย่างน้อย 3 ตัวอักษร', 'error')
                return redirect(url_for('auth.select_company'))

            # ปรับให้ทุกบริษัทไม่ active ก่อน
            UserCompany.query.filter_by(user_id=current_user.id).update({'active_company': False})

            # สร้างบริษัทใหม่
            company = Company(
                name=company_name,
                created_at=datetime.now(bangkok_tz),
                owner_id=current_user.id,
            )
            db.session.add(company)
            db.session.commit()

            # สร้างความสัมพันธ์กับผู้ใช้
            user_company = UserCompany(
                user_id=current_user.id,
                company_id=company.id,
                is_admin=True,
                active_company=True
            )
            db.session.add(user_company)
            db.session.commit()

            # สร้างหมวดหมู่และบัญชีธนาคารเริ่มต้น
            create_default_categories(current_user.id, company.id)
            create_default_bank_account(current_user.id, company.id)

            flash(f'สร้างบริษัท {company.name} เรียบร้อยแล้ว', 'success')
            return redirect(url_for('main.dashboard'))
    return render_template('auth/select_company.html', user_companies=user_companies, is_select_company_page=True)


@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('main.index'))


# Helper functions

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
            company_id=company_id
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
        company_id=company_id
    )
    db.session.add(default_account)
    db.session.commit()


def process_invite_token(token, user_id, is_new_user=False):
    """จัดการ invite token และเชื่อมโยงผู้ใช้กับบริษัท"""
    invite = InviteToken.query.filter_by(token=token, used=False).first()
    if invite:
        # อัปเดตสถานะของคำเชิญเป็นใช้แล้ว
        invite.used = True
        invite.used_by = user_id

        # ถ้ามีการเชื่อมโยงกับบริษัท
        if invite.company_id:
            # ตรวจสอบว่าผู้ใช้เป็นสมาชิกของบริษัทนี้อยู่แล้วหรือไม่
            existing_relation = UserCompany.query.filter_by(
                user_id=user_id,
                company_id=invite.company_id
            ).first()

            if existing_relation:
                # ถ้าเป็นสมาชิกอยู่แล้ว ให้กำหนดเป็นบริษัทที่ active
                UserCompany.query.filter_by(user_id=user_id).update({'active_company': False})
                existing_relation.active_company = True
            else:
                # ถ้ายังไม่เป็นสมาชิก ให้สร้างความสัมพันธ์ใหม่
                # ยกเลิก active ของทุกบริษัทก่อน
                UserCompany.query.filter_by(user_id=user_id).update({'active_company': False})

                # สร้างความสัมพันธ์ใหม่
                user_company = UserCompany(
                    user_id=user_id,
                    company_id=invite.company_id,
                    is_admin=False,  # เริ่มต้นไม่เป็นแอดมิน
                    active_company=True  # กำหนดเป็นบริษัทที่ active
                )
                db.session.add(user_company)

        db.session.commit()
        return True

    return False


# Helper function เพื่อดึงบริษัทที่ active ของผู้ใช้
def get_active_company():
    user_company = UserCompany.query.filter_by(
        user_id=current_user.id,
        active_company=True
    ).first()

    if not user_company:
        # ถ้าไม่มีบริษัทที่ active ให้เลือกบริษัทแรก (ถ้ามี)
        user_company = UserCompany.query.filter_by(user_id=current_user.id).first()

        if user_company:
            user_company.active_company = True
            db.session.commit()

    return user_company.company if user_company else None


# Helper function เพื่อตรวจสอบว่าผู้ใช้เป็นแอดมินของบริษัทหรือไม่
def is_company_admin(company_id):
    user_company = UserCompany.query.filter_by(
        user_id=current_user.id,
        company_id=company_id,
        is_admin=True
    ).first()

    return user_company is not None