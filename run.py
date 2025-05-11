# run.py
import os
import pymysql
import time
import logging
from sqlalchemy.exc import OperationalError

# ทำให้ PyMySQL จำลองตัวเองเป็น MySQLdb
pymysql.install_as_MySQLdb()

from app import create_app, db
import os

# ตั้งค่าการบันทึกล็อก
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = create_app()

# CLI command สำหรับสร้างฐานข้อมูล
@app.cli.command("init-db")
def init_db():
    """Initialize the database."""
    try:
        # พยายามเชื่อมต่อกับฐานข้อมูล
        with app.app_context():
            db.create_all()
            print("Database tables created successfully.")
    except Exception as e:
        print(f"Error creating database tables: {str(e)}")
        raise

# คำสั่ง cli สำหรับทดสอบการเชื่อมต่อฐานข้อมูล
@app.cli.command("test-db")
def test_db():
    """Test database connection."""
    try:
        with app.app_context():
            result = db.session.execute("SELECT 1")
            print("Database connection successful!")
    except Exception as e:
        print(f"Database connection error: {str(e)}")

# ตรวจสอบสภาพแวดล้อม Digital Ocean
@app.cli.command("check-env")
def check_env():
    """Check environment variables and settings."""
    print(f"FLASK_ENV: {os.environ.get('FLASK_ENV', 'not set')}")
    print(f"UPLOAD_FOLDER: {app.config.get('UPLOAD_FOLDER', 'not set')}")
    print(f"DATABASE_URL: {os.environ.get('DATABASE_URL', 'not set')[:20]}...")  # แสดงเฉพาะส่วนต้น

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('FLASK_ENV') == 'development'
    app.run(host='0.0.0.0', port=port, debug=debug)