# run.py
import pymysql
import time
import logging
from sqlalchemy.exc import OperationalError

# ทำให้ PyMySQL จำลองตัวเองเป็น MySQLdb
pymysql.install_as_MySQLdb()

from app import create_app
from app.models import db
import os

# ตั้งค่าการบันทึกล็อก
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = create_app()


# เพิ่มฟังก์ชัน retry สำหรับการเชื่อมต่อฐานข้อมูล
def try_db_connection(max_retries=5, delay=5):
    """พยายามเชื่อมต่อกับฐานข้อมูลหลายครั้งหากจำเป็น"""
    retry_count = 0
    last_error = None

    while retry_count < max_retries:
        try:
            with app.app_context():
                # พยายามเชื่อมต่อและสร้างตาราง
                db.engine.connect()
                logger.info("✅ Database connection successful!")
                return True
        except Exception as e:
            last_error = e
            retry_count += 1
            logger.warning(f"Database connection attempt {retry_count} failed: {str(e)}")
            if retry_count < max_retries:
                logger.info(f"Retrying in {delay} seconds...")
                time.sleep(delay)

    logger.error(f"❌ Failed to connect to database after {max_retries} attempts: {str(last_error)}")
    return False


# สร้างฐานข้อมูลในการเริ่มแอป
@app.before_first_request
def initialize_database():
    if try_db_connection():
        # เมื่อเชื่อมต่อสำเร็จ ให้ตรวจสอบและสร้างตาราง
        try:
            with app.app_context():
                db.create_all()
                logger.info("✅ Database tables created or already exist")
        except Exception as e:
            logger.error(f"❌ Error creating database tables: {str(e)}")


# CLI command สำหรับสร้างฐานข้อมูล
@app.cli.command("init-db")
def init_db():
    """Initialize the database."""
    if try_db_connection():
        with app.app_context():
            db.create_all()
            print("✅ Database tables created successfully.")


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)