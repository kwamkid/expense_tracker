import pytesseract
from PIL import Image
import cv2
import numpy as np

# ระบุตำแหน่งของ Tesseract
pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'

# ตรวจสอบเวอร์ชันและภาษาที่ติดตั้ง
print("Tesseract Version:", pytesseract.get_tesseract_version())
print("Available Languages:", pytesseract.get_languages())

# ทดสอบกับไฟล์ภาพใบเสร็จของคุณ
image_path = 'app/static/uploads/receipts/POS.png'  # แก้ไขเป็นพาธของไฟล์ใบเสร็จของคุณ

# อ่านภาพ
image = cv2.imread(image_path)

# แปลงเป็นภาพขาวดำ
gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

# ปรับปรุงภาพ (เพิ่มความคมชัด)
gray = cv2.GaussianBlur(gray, (3, 3), 0)
gray = cv2.adaptiveThreshold(gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, 11, 2)

# แปลงเป็น PIL Image
pil_image = Image.fromarray(gray)

# ทดสอบ OCR กับภาษาไทยและอังกฤษ
print("\nกำลังประมวลผล OCR...")
text = pytesseract.image_to_string(pil_image, lang='tha+eng')

# แสดงผลที่ได้
print("\nผลลัพธ์ OCR:")
print("="*50)
print(text)
print("="*50)