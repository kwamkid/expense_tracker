import os
import re
import cv2
import numpy as np
import pytesseract
from datetime import datetime
from PIL import Image
from flask import current_app


class ReceiptOCR:
    def __init__(self, image_path):
        """
        สร้างอินสแตนซ์ OCR สำหรับประมวลผลใบเสร็จ

        Args:
            image_path (str): พาธของไฟล์ภาพใบเสร็จ
        """
        self.image_path = image_path
        self.text = None
        self.preprocessed_image = None
        self.extracted_data = {
            'date': None,
            'total_amount': None,
            'vendor': None,
            'items': [],
            'receipt_no': None
        }

    def preprocess_image(self):
        """ปรับปรุงคุณภาพภาพเพื่อเพิ่มความแม่นยำของ OCR"""
        # อ่านภาพด้วย OpenCV
        image = cv2.imread(self.image_path)

        # แปลงเป็นภาพขาวดำ
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # ปรับความสว่างและคอนทราสต์
        # Apply adaptive thresholding
        thresh = cv2.adaptiveThreshold(
            gray, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 11, 2
        )

        # ลดสัญญาณรบกวน
        kernel = np.ones((1, 1), np.uint8)
        opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

        self.preprocessed_image = opening
        return opening

    def perform_ocr(self):
        """ดำเนินการ OCR บนภาพที่ผ่านการปรับปรุงแล้ว"""
        if self.preprocessed_image is None:
            self.preprocess_image()

        # แปลงภาพ OpenCV เป็น PIL Image
        pil_image = Image.fromarray(self.preprocessed_image)

        # ดำเนินการ OCR
        custom_config = r'--oem 3 --psm 6'
        self.text = pytesseract.image_to_string(pil_image, lang='tha+eng', config=custom_config)

        return self.text

    def extract_date(self):
        """ดึงวันที่จากข้อความใบเสร็จ"""
        if not self.text:
            self.perform_ocr()

        # รูปแบบวันที่ไทย (เช่น 01/01/2566, 01-01-2566)
        date_patterns = [
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})',  # DD/MM/YYYY or DD-MM-YYYY
            r'(\d{1,2}\s+(?:ม\.?ค\.?|ก\.?พ\.?|มี\.?ค\.?|เม\.?ย\.?|พ\.?ค\.?|มิ\.?ย\.?|ก\.?ค\.?|ส\.?ค\.?|ก\.?ย\.?|ต\.?ค\.?|พ\.?ย\.?|ธ\.?ค\.?)\s+\d{4})',
            # DD เดือนไทย YYYY
            r'(วันที่\s*\d{1,2}[/-]\d{1,2}[/-]\d{4})',  # วันที่ DD/MM/YYYY
            r'Date:?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4})'  # Date: DD/MM/YYYY
        ]

        for pattern in date_patterns:
            matches = re.search(pattern, self.text)
            if matches:
                date_str = matches.group(1)

                # แปลงเป็นรูปแบบวันที่มาตรฐาน (YYYY-MM-DD)
                try:
                    # แปลงปี พ.ศ. เป็น ค.ศ. ถ้าจำเป็น
                    if re.search(r'\d{4}', date_str).group(0) > '2500':
                        date_str = re.sub(r'(\d{1,2}[/-]\d{1,2}[/-])(\d{4})',
                                          lambda m: m.group(1) + str(int(m.group(2)) - 543),
                                          date_str)

                    # ลองแปลงรูปแบบวันที่ต่างๆ
                    formats = ['%d/%m/%Y', '%d-%m-%Y', '%d %b %Y']
                    for fmt in formats:
                        try:
                            date_obj = datetime.strptime(date_str, fmt)
                            self.extracted_data['date'] = date_obj.strftime('%Y-%m-%d')
                            return self.extracted_data['date']
                        except ValueError:
                            continue
                except Exception as e:
                    current_app.logger.error(f"Error parsing date: {e}")

        return None

    def extract_total_amount(self):
        """ดึงจำนวนเงินรวมจากข้อความใบเสร็จ"""
        if not self.text:
            self.perform_ocr()

        # รูปแบบจำนวนเงินรวม
        amount_patterns = [
            r'(?:รวมทั้งสิ้น|รวมเงิน|ยอดรวม|TOTAL|GRAND TOTAL)[^\d]*?(\d+(?:[.,]\d{1,2})?)',
            r'(?:จำนวนเงิน|AMOUNT)[^\d]*?(\d+(?:[.,]\d{1,2})?)',
            r'(?:NET AMOUNT|NET)[^\d]*?(\d+(?:[.,]\d{1,2})?)',
            r'(?<=TOTAL\s)(\d+(?:[.,]\d{1,2})?)',
            r'(?<=รวม\s)(\d+(?:[.,]\d{1,2})?)'
        ]

        for pattern in amount_patterns:
            matches = re.search(pattern, self.text, re.IGNORECASE)
            if matches:
                amount_str = matches.group(1).strip()

                # แปลงเป็นตัวเลข
                try:
                    # ลบตัวอักษรที่ไม่ใช่ตัวเลขและจุดทศนิยม
                    amount_str = re.sub(r'[^\d.]', '', amount_str)
                    amount = float(amount_str)
                    self.extracted_data['total_amount'] = amount
                    return amount
                except Exception as e:
                    current_app.logger.error(f"Error parsing amount: {e}")

        return None

    def extract_vendor(self):
        """ดึงชื่อร้านค้า/ผู้ขายจากข้อความใบเสร็จ"""
        if not self.text:
            self.perform_ocr()

        # ชื่อร้านค้ามักจะอยู่ในบรรทัดแรกๆ ของใบเสร็จ
        lines = self.text.split('\n')

        # ตัดบรรทัดว่างออก
        lines = [line.strip() for line in lines if line.strip()]

        if lines:
            # ใช้บรรทัดแรกหรือบรรทัดที่สองเป็นชื่อร้านค้า
            vendor = lines[0]

            # ตรวจสอบว่าบรรทัดแรกเป็นชื่อร้านค้าจริงๆ (ไม่ใช่คำเช่น "ใบเสร็จรับเงิน")
            if re.search(r'(?:ใบเสร็จ|ใบกำกับ|RECEIPT|INVOICE)', vendor, re.IGNORECASE):
                if len(lines) > 1:
                    vendor = lines[1]

            self.extracted_data['vendor'] = vendor
            return vendor

        return None

    def extract_all_data(self):
        """ดึงข้อมูลทั้งหมดจากใบเสร็จ"""
        if not self.text:
            self.perform_ocr()

        self.extract_date()
        self.extract_total_amount()
        self.extract_vendor()
        # สามารถเพิ่มเมธอดสำหรับดึงข้อมูลอื่นๆ เช่น รายการสินค้า, เลขที่ใบเสร็จ ฯลฯ

        return self.extracted_data


def process_receipt_image(image_path):
    """
    ฟังก์ชันหลักสำหรับประมวลผลภาพใบเสร็จและดึงข้อมูล

    Args:
        image_path (str): พาธของไฟล์ภาพใบเสร็จ

    Returns:
        dict: ข้อมูลที่ดึงได้จากใบเสร็จ
    """
    receipt_ocr = ReceiptOCR(image_path)
    receipt_ocr.preprocess_image()
    receipt_ocr.perform_ocr()
    extracted_data = receipt_ocr.extract_all_data()

    return extracted_data