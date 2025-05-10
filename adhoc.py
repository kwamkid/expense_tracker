# migration_script.py
# สคริปต์นี้จะย้ายบัญชีธนาคารที่ยังไม่มี company_id ให้เชื่อมโยงกับบริษัท
# วิธีใช้: ให้รัน python migration_script.py ในโฟลเดอร์หลักของแอพ
from flask import Flask
from app.models import db, BankAccount, UserCompany
import logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def create_app():
    from app.config import Config
    app = Flask(__name__)
    app.config.from_object(Config)
    db.init_app(app)
    return app


def migrate_bank_accounts():
    """ย้ายบัญชีธนาคารที่ยังไม่มี company_id ให้เชื่อมโยงกับบริษัท"""
    try:
        # ดึงบัญชีธนาคารที่ยังไม่มี company_id
        bank_accounts_without_company = BankAccount.query.filter(BankAccount.company_id == None).all()

        logger.info(f"พบบัญชีธนาคารที่ยังไม่มี company_id จำนวน {len(bank_accounts_without_company)} รายการ")

        migrated_count = 0
        errors_count = 0

        for bank_account in bank_accounts_without_company:
            try:
                # ค้นหาบริษัทที่ active ของเจ้าของบัญชี
                user_company = UserCompany.query.filter_by(
                    user_id=bank_account.user_id,
                    active_company=True
                ).first()

                if not user_company:
                    # ถ้าไม่มีบริษัทที่ active ให้ดึงบริษัทแรกที่ผู้ใช้เป็นสมาชิก
                    user_company = UserCompany.query.filter_by(
                        user_id=bank_account.user_id
                    ).first()

                if user_company:
                    # อัปเดตบัญชีธนาคาร
                    bank_account.company_id = user_company.company_id
                    logger.info(
                        f"อัปเดตบัญชีธนาคาร ID {bank_account.id} ให้เชื่อมโยงกับบริษัท ID {user_company.company_id}")
                    migrated_count += 1
                else:
                    logger.warning(
                        f"ไม่พบบริษัทสำหรับผู้ใช้ ID {bank_account.user_id} ของบัญชีธนาคาร ID {bank_account.id}")
                    errors_count += 1
            except Exception as e:
                logger.error(f"เกิดข้อผิดพลาดในการย้ายบัญชีธนาคาร ID {bank_account.id}: {str(e)}")
                errors_count += 1

        # บันทึกการเปลี่ยนแปลง
        db.session.commit()
        logger.info(f"สำเร็จ: อัปเดตบัญชีธนาคารแล้ว {migrated_count} รายการ, ผิดพลาด {errors_count} รายการ")

        return migrated_count, errors_count
    except Exception as e:
        db.session.rollback()
        logger.error(f"เกิดข้อผิดพลาดในการย้ายข้อมูล: {str(e)}")
        return 0, 0


def check_orphaned_transactions():
    """ตรวจสอบรายการธุรกรรมที่อ้างถึงบัญชีธนาคารซึ่งอยู่คนละบริษัท"""
    from app.models import Transaction

    try:
        # ดึงรายการธุรกรรมที่มีบัญชีธนาคาร
        transactions = Transaction.query.filter(Transaction.bank_account_id != None).all()

        mismatched_count = 0
        for transaction in transactions:
            if transaction.bank_account and transaction.company_id != transaction.bank_account.company_id:
                logger.warning(
                    f"พบรายการธุรกรรม ID {transaction.id} ที่อ้างถึงบัญชีธนาคาร ID {transaction.bank_account_id} ซึ่งอยู่ต่างบริษัทกัน")
                mismatched_count += 1

        logger.info(f"ตรวจพบรายการธุรกรรมที่อ้างถึงบัญชีธนาคารต่างบริษัทกัน จำนวน {mismatched_count} รายการ")
        return mismatched_count
    except Exception as e:
        logger.error(f"เกิดข้อผิดพลาดในการตรวจสอบรายการธุรกรรม: {str(e)}")
        return 0


def main():
    app = create_app()
    with app.app_context():
        logger.info("เริ่มต้นการย้ายข้อมูลบัญชีธนาคารเข้าสู่บริษัท")
        migrated, errors = migrate_bank_accounts()
        logger.info(f"สรุปผลการย้ายข้อมูล: สำเร็จ {migrated} รายการ, ผิดพลาด {errors} รายการ")

        orphaned = check_orphaned_transactions()
        logger.info(f"รายการธุรกรรมที่อาจมีปัญหา: {orphaned} รายการ")


if __name__ == "__main__":
    main()