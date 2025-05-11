import os
import pymysql
from dotenv import load_dotenv
import sys

# โหลด environment variables
load_dotenv()

# ตรวจสอบ DATABASE_URL จาก environment
db_url = os.environ.get('DATABASE_URL')

if not db_url:
    print("DATABASE_URL not set in environment")
    sys.exit(1)

# แยกชิ้นส่วน URL เพื่อเชื่อมต่อ
try:
    # ใช้โค้ดเดียวกับด้านบนเพื่อแยก connection parameters
    cleaned_url = db_url.replace('mysql+pymysql://', '').replace('mysql://', '')
    auth, host_part = cleaned_url.split('@')

    if ':' in auth:
        username, password = auth.split(':')
    else:
        username = auth
        password = ''

    host_info, db_name_part = host_part.split('/', 1)

    if ':' in host_info:
        host, port_str = host_info.split(':')
        port = int(port_str)
    else:
        host = host_info
        port = 3306

    if '?' in db_name_part:
        db_name = db_name_part.split('?')[0]
    else:
        db_name = db_name_part

    # เชื่อมต่อฐานข้อมูล
    conn = pymysql.connect(
        host=host,
        user=username,
        password=password,
        database=db_name,
        port=port,
        connect_timeout=10
    )

    # สร้างตารางที่จำเป็น (จากโครงสร้างใน models.py)
    with conn.cursor() as cursor:
        # สร้างตาราง company ก่อนเพราะมี FK references
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS company (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(200),
            address TEXT,
            tax_id VARCHAR(20),
            logo_path VARCHAR(255),
            created_at DATETIME,
            owner_id INT
        )
        """)

        # สร้างตาราง user
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user (
            id INT AUTO_INCREMENT PRIMARY KEY,
            line_id VARCHAR(100) NOT NULL UNIQUE,
            name VARCHAR(100),
            picture_url VARCHAR(255),
            email VARCHAR(120),
            created_at DATETIME,
            company_id INT,
            company_name VARCHAR(200),
            company_address TEXT,
            tax_id VARCHAR(20),
            logo_path VARCHAR(255),
            FOREIGN KEY (company_id) REFERENCES company(id)
        )
        """)

        # สร้างตาราง user_company
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS user_company (
            id INT AUTO_INCREMENT PRIMARY KEY,
            user_id INT NOT NULL,
            company_id INT NOT NULL,
            is_admin BOOLEAN DEFAULT FALSE,
            active_company BOOLEAN DEFAULT TRUE,
            joined_at DATETIME,
            UNIQUE(user_id, company_id),
            FOREIGN KEY (user_id) REFERENCES user(id),
            FOREIGN KEY (company_id) REFERENCES company(id)
        )
        """)

        # สร้างตาราง bank_account
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS bank_account (
            id INT AUTO_INCREMENT PRIMARY KEY,
            bank_name VARCHAR(100) NOT NULL,
            account_number VARCHAR(20) NOT NULL,
            account_name VARCHAR(200),
            initial_balance FLOAT DEFAULT 0.0,
            current_balance FLOAT DEFAULT 0.0,
            is_active BOOLEAN DEFAULT TRUE,
            created_at DATETIME,
            user_id INT NOT NULL,
            company_id INT,
            FOREIGN KEY (user_id) REFERENCES user(id),
            FOREIGN KEY (company_id) REFERENCES company(id)
        )
        """)

        # สร้างตาราง category
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS category (
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            type VARCHAR(10) NOT NULL,
            keywords TEXT,
            user_id INT NOT NULL,
            company_id INT,
            FOREIGN KEY (user_id) REFERENCES user(id),
            FOREIGN KEY (company_id) REFERENCES company(id)
        )
        """)

        # สร้างตาราง transaction
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS transaction (
            id INT AUTO_INCREMENT PRIMARY KEY,
            amount FLOAT NOT NULL,
            description TEXT,
            transaction_date DATE NOT NULL,
            type VARCHAR(10) NOT NULL,
            status VARCHAR(20) DEFAULT 'pending',
            transaction_time TIME,
            completed_date DATETIME,
            source VARCHAR(20) DEFAULT 'manual',
            bank_account_id INT,
            bank_reference VARCHAR(100),
            import_batch_id VARCHAR(50),
            created_at DATETIME,
            user_id INT NOT NULL,
            category_id INT NOT NULL,
            company_id INT,
            FOREIGN KEY (bank_account_id) REFERENCES bank_account(id),
            FOREIGN KEY (user_id) REFERENCES user(id),
            FOREIGN KEY (category_id) REFERENCES category(id),
            FOREIGN KEY (company_id) REFERENCES company(id)
        )
        """)

        # สร้างตาราง invite_token
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS invite_token (
            id INT AUTO_INCREMENT PRIMARY KEY,
            token VARCHAR(100) NOT NULL UNIQUE,
            created_by INT NOT NULL,
            created_at DATETIME,
            used BOOLEAN DEFAULT FALSE,
            used_by INT,
            company_id INT,
            FOREIGN KEY (created_by) REFERENCES user(id),
            FOREIGN KEY (used_by) REFERENCES user(id),
            FOREIGN KEY (company_id) REFERENCES company(id)
        )
        """)

        # สร้างตาราง import_history
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS import_history (
            id INT AUTO_INCREMENT PRIMARY KEY,
            batch_id VARCHAR(50) NOT NULL UNIQUE,
            filename VARCHAR(255) NOT NULL,
            bank_type VARCHAR(50) NOT NULL,
            import_date DATETIME,
            transaction_count INT DEFAULT 0,
            total_amount FLOAT DEFAULT 0,
            status VARCHAR(20) DEFAULT 'completed',
            user_id INT NOT NULL,
            bank_account_id INT,
            company_id INT,
            FOREIGN KEY (user_id) REFERENCES user(id),
            FOREIGN KEY (bank_account_id) REFERENCES bank_account(id),
            FOREIGN KEY (company_id) REFERENCES company(id)
        )
        """)

    # Commit การเปลี่ยนแปลง
    conn.commit()
    print("All tables created successfully!")

    # ปิดการเชื่อมต่อ
    conn.close()

except Exception as e:
    print(f"Error creating tables: {str(e)}")
    sys.exit(1)