import os
import pymysql
from dotenv import load_dotenv

# โหลด environment variables
load_dotenv()

# ตรวจสอบ DATABASE_URL จาก environment
db_url = os.environ.get('DATABASE_URL')
print(f"DATABASE_URL: {db_url[:20]}..." if db_url else "DATABASE_URL not set")

# แยกชิ้นส่วน URL เพื่อเชื่อมต่อ
try:
    if db_url and db_url.startswith('mysql'):
        # แยก URL เพื่อดึงข้อมูลเชื่อมต่อ
        cleaned_url = db_url.replace('mysql+pymysql://', '').replace('mysql://', '')

        # แยกส่วน username:password และ host/database
        if '@' in cleaned_url:
            auth, host_part = cleaned_url.split('@')

            # แยก username และ password
            if ':' in auth:
                username, password = auth.split(':')
            else:
                username = auth
                password = ''

            # แยก host และ database
            if '/' in host_part:
                host_info, db_name_part = host_part.split('/', 1)

                # แยก host และ port
                if ':' in host_info:
                    host, port_str = host_info.split(':')
                    port = int(port_str)
                else:
                    host = host_info
                    port = 3306

                # ดึงชื่อฐานข้อมูล (ตัดพารามิเตอร์ออก)
                if '?' in db_name_part:
                    db_name = db_name_part.split('?')[0]
                else:
                    db_name = db_name_part

                print(f"Connecting to MySQL at {host}:{port}")
                print(f"Username: {username}")
                print(f"Database name: {db_name}")

                # ทดลองเชื่อมต่อ
                try:
                    conn = pymysql.connect(
                        host=host,
                        user=username,
                        password=password,
                        database=db_name,
                        port=port,
                        connect_timeout=10
                    )
                    print("Database connection successful!")

                    # ตรวจสอบตารางที่มี
                    with conn.cursor() as cursor:
                        cursor.execute("SHOW TABLES")
                        tables = cursor.fetchall()
                        if tables:
                            print(f"Found {len(tables)} tables:")
                            for table in tables:
                                print(f"- {table[0]}")
                        else:
                            print("No tables found in the database.")

                    # ทดลองตรวจสอบการมีอยู่ของตาราง user
                    try:
                        with conn.cursor() as cursor:
                            cursor.execute("SELECT 1 FROM user LIMIT 1")
                            result = cursor.fetchone()
                            print("Table 'user' exists and is accessible.")
                    except Exception as e:
                        print(f"Error accessing 'user' table: {str(e)}")

                    conn.close()

                except Exception as e:
                    print(f"Database connection error: {str(e)}")
            else:
                print("Invalid DATABASE_URL format: missing database name")
        else:
            print("Invalid DATABASE_URL format: missing @ separator")
    else:
        print("DATABASE_URL not found or not MySQL format")
except Exception as e:
    print(f"Error parsing DATABASE_URL: {str(e)}")