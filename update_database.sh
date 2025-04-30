#!/bin/bash
# สคริปต์สำหรับอัปเดต Migration และฐานข้อมูล
# ใช้งานโดย: ./update_database.sh

# แสดงข้อความว่ากำลังสำรองฐานข้อมูล
echo "กำลังสำรองฐานข้อมูล..."
mkdir -p backups
cp instance/app.db backups/app.db.$(date +"%Y%m%d%H%M%S")
echo "สำรองฐานข้อมูลเรียบร้อยแล้ว"

# สร้าง Migration ใหม่
echo "กำลังสร้าง Migration..."
flask db migrate -m "Add fields for import transaction feature and account number"

# แสดงข้อความแจ้งเตือนให้ตรวจสอบไฟล์ Migration
echo ""
echo "--------------------------------------------------------------"
echo "โปรดตรวจสอบไฟล์ Migration ล่าสุดที่สร้างขึ้นใน migrations/versions/"
echo "เพื่อให้แน่ใจว่าการเปลี่ยนแปลงถูกต้อง"
echo ""
echo "รายการเปลี่ยนแปลงที่ควรมี:"
echo "- เพิ่มคอลัมน์ transaction_hash ในตาราง transactions"
echo "- เพิ่มคอลัมน์ bank_reference ในตาราง transactions"
echo "- เพิ่มคอลัมน์ imported_from ในตาราง transactions"
echo "- เพิ่มคอลัมน์ import_batch_id ในตาราง transactions"
echo "- เพิ่มคอลัมน์ account_number ในตาราง accounts"
echo "- เพิ่มคอลัมน์ bank_name ในตาราง accounts"
echo "- สร้างตาราง category_keywords"
echo "- สร้างตาราง import_batches"
echo "- สร้างตาราง transaction_category_history"
echo "--------------------------------------------------------------"

# ถามว่าต้องการดำเนินการ upgrade หรือไม่
read -p "ทำการอัปเกรดฐานข้อมูลหรือไม่? (y/n): " choice
if [ "$choice" = "y" ] || [ "$choice" = "Y" ]; then
    # อัปเกรดฐานข้อมูล
    echo "กำลังอัปเกรดฐานข้อมูล..."
    flask db upgrade
    echo "อัปเกรดฐานข้อมูลเรียบร้อยแล้ว"
else
    echo "ยกเลิกการอัปเกรดฐานข้อมูล"
fi

echo ""
echo "เสร็จสิ้นการทำงาน"