from app import create_app, db
from app.models import User, Company, UserCompany
import logging

# ตั้งค่า logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = create_app()

def migrate_user_company_data():
    """ย้ายข้อมูลความสัมพันธ์ระหว่างผู้ใช้และบริษัทไปยังโมเดลใหม่"""
    with app.app_context():
        # ย้ายข้อมูลผู้ใช้ที่มี company_id
        users = User.query.filter(User.company_id.isnot(None)).all()
        
        logger.info(f"Found {len(users)} users with company relationships to migrate")
        
        for user in users:
            # ตรวจสอบว่ามีความสัมพันธ์ในตาราง UserCompany หรือยัง
            existing = UserCompany.query.filter_by(user_id=user.id, company_id=user.company_id).first()
            
            if not existing:
                # ตรวจสอบว่าบริษัทมีอยู่จริงหรือไม่
                company = Company.query.get(user.company_id)
                if not company:
                    logger.warning(f"Warning: Company ID {user.company_id} not found for user {user.id}")
                    continue
                    
                # สร้างความสัมพันธ์ใหม่
                uc = UserCompany(
                    user_id=user.id,
                    company_id=user.company_id,
                    is_admin=company.owner_id == user.id,  # ตั้งเป็นแอดมินถ้าเป็นเจ้าของบริษัท
                    active_company=False  # ตั้งเป็น False เพื่อบังคับให้ต้องเลือก
                )
                db.session.add(uc)
                logger.info(f"Created new relationship: User {user.id} -> Company {company.id} ({company.name})")
            else:
                logger.info(f"Relationship already exists: User {user.id} -> Company {existing.company.id} ({existing.company.name})")
        
        db.session.commit()
        logger.info("Migration completed successfully")


if __name__ == "__main__":
    migrate_user_company_data()