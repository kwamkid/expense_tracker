# Simple Expense Tracker

ระบบบันทึกรายรับรายจ่ายอย่างง่าย พร้อมระบบนำเข้าข้อมูลจากธนาคาร

## Features

- เข้าสู่ระบบด้วย LINE Login
- บันทึกรายรับรายจ่าย
- นำเข้าข้อมูลจากไฟล์ Excel ของธนาคาร (SCB, KBANK, BBL, BAY)
- แยกหมวดหมู่อัตโนมัติ
- รายงานและกราฟแสดงผล
- ตั้งค่าข้อมูลบริษัท (โลโก้, ที่อยู่, เลขผู้เสียภาษี)
- เชิญผู้ใช้ผ่านลิงก์

## Installation

1. Clone repository
2. Create virtual environment: `python -m venv venv`
3. Activate virtual environment: `source venv/bin/activate`
4. Install dependencies: `pip install -r requirements.txt`
5. Copy `.env.example` to `.env` and update values
6. Initialize database: `flask db upgrade`
7. Run: `flask run`

## Deployment to Digital Ocean

1. Create App Platform application
2. Connect to your GitHub repository
3. Set environment variables
4. Deploy

## License

MIT