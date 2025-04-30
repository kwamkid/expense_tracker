# create_admin.py
from app import create_app
from app.extensions import db
from app.models.user import User
from app.models.organization import Organization, organization_users
from app.views.auth import create_default_categories
from app.views.organization import create_default_account
from datetime import datetime

app = create_app()

with app.app_context():
    # ตรวจสอบว่ามีผู้ใช้อยู่แล้วหรือไม่
    if User.query.filter_by(email='admin@example.com').first() is None:
        # สร้างผู้ใช้แอดมิน
        admin_user = User(
            username='admin',
            email='admin@example.com',
            password='admin123',  # ในโปรดักชันควรใช้รหัสผ่านที่รัดกุมกว่านี้
            first_name='Admin',
            last_name='User'
        )
        db.session.add(admin_user)
        db.session.flush()  # เพื่อให้ได้ ID ของผู้ใช้

        # สร้างองค์กรเริ่มต้น
        organization = Organization(
            name='องค์กรเริ่มต้น',
            description='องค์กรเริ่มต้นสำหรับทดสอบระบบ',
            created_by=admin_user.id
        )
        db.session.add(organization)
        db.session.flush()

        # เพิ่มผู้ใช้เป็นแอดมินขององค์กร
        db.session.execute(
            organization_users.insert().values(
                user_id=admin_user.id,
                organization_id=organization.id,
                role='admin',
                joined_at=datetime.utcnow()
            )
        )

        # ตั้งค่าองค์กรที่ใช้งานอยู่
        admin_user.active_organization_id = organization.id

        # สร้างหมวดหมู่เริ่มต้น
        create_default_categories(organization.id, admin_user.id)

        # สร้างบัญชีเริ่มต้น
        create_default_account(organization.id, admin_user.id)

        db.session.commit()
        print("Admin user, organization, categories and account created successfully!")
    else:
        print("Admin user already exists!")