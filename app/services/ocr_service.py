import os
import re
import cv2
import numpy as np
import pytesseract
from datetime import datetime
from PIL import Image, ImageEnhance
from flask import current_app


# กำหนดตำแหน่งของ Tesseract
pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'

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
        """ปรับปรุงคุณภาพภาพเพื่อเพิ่มความแม่นยำของ OCR สำหรับภาษาไทย"""
        # อ่านภาพด้วย OpenCV
        image = cv2.imread(self.image_path)

        # สร้างสำเนาของภาพต้นฉบับ
        original = image.copy()

        # แปลงเป็นภาพขาวดำ
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

        # ใช้ bilateral filter เพื่อลดสัญญาณรบกวนแต่รักษาขอบ (เหมาะกับตัวอักษรไทย)
        blur = cv2.bilateralFilter(gray, 9, 75, 75)

        # เพิ่มความคมชัดของขอบ
        kernel = np.array([[-1, -1, -1], [-1, 9, -1], [-1, -1, -1]])
        sharp = cv2.filter2D(blur, -1, kernel)

        # ปรับความสว่างและคอนทราสต์ด้วย CLAHE
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(sharp)

        # ปรับ threshold แบบ adaptive (เหมาะกับตัวอักษรไทยที่มีเส้นบาง)
        thresh = cv2.adaptiveThreshold(
            enhanced, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
            cv2.THRESH_BINARY, 21, 11  # ขยาย block size เพื่อรองรับข้อความขนาดใหญ่
        )

        # ลดสัญญาณรบกวนเล็กๆ
        kernel = np.ones((1, 1), np.uint8)
        opening = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)

        # ขยายตัวอักษรเล็กน้อยเพื่อให้อ่านง่ายขึ้น
        kernel = np.ones((1, 1), np.uint8)
        dilation = cv2.dilate(opening, kernel, iterations=1)

        # เก็บภาพที่ผ่านการประมวลผล
        self.preprocessed_image = dilation

        # สร้างภาพที่ผ่านการประมวลผลหลายแบบ เพื่อให้มีโอกาสอ่านได้ถูกต้องมากขึ้น
        self.multi_processed_images = {
            'original_gray': gray,
            'enhanced': enhanced,
            'threshold': thresh,
            'dilated': dilation
        }

        return self.preprocessed_image

    def perform_ocr(self):
        """ดำเนินการ OCR บนภาพที่ผ่านการปรับปรุงแล้ว โดยเน้นความสามารถในการอ่านภาษาไทย"""
        if self.preprocessed_image is None:
            self.preprocess_image()

        # ตรวจสอบว่ามีการติดตั้งภาษาไทยสำหรับ Tesseract
        try:
            # แปลงภาพ OpenCV เป็น PIL Image
            pil_image = Image.fromarray(self.preprocessed_image)

            # ปรับขนาดภาพให้ใหญ่ขึ้น (ช่วยให้อ่านตัวอักษรขนาดเล็กได้ดีขึ้น)
            width, height = pil_image.size
            pil_image = pil_image.resize((width * 2, height * 2), Image.LANCZOS)

            # ตรวจสอบให้แน่ใจว่าใช้ตำแหน่ง Tesseract ที่ถูกต้อง
            pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'

            # ทดลองอ่านด้วยการตั้งค่าที่เหมาะกับใบเสร็จภาษาไทย
            # --oem 1: LSTM OCR Engine (แม่นยำกว่าสำหรับภาษาไทย)
            # --psm 6: Assume a single uniform block of text
            custom_config = r'--oem 1 --psm 6'
            self.text = pytesseract.image_to_string(pil_image, lang='tha+eng', config=custom_config)

            # หากไม่พบข้อมูล ลองใช้โหมด PSM อื่น
            if not self._has_useful_data(self.text):
                # --psm 4: Assume a single column of text of variable sizes
                custom_config = r'--oem 1 --psm 4'
                text2 = pytesseract.image_to_string(pil_image, lang='tha+eng', config=custom_config)
                if self._has_useful_data(text2):
                    self.text = text2

            # ลองใช้ภาพที่ผ่านการประมวลผลในแบบอื่นๆ
            for img_type, img in self.multi_processed_images.items():
                if not self._has_useful_data(self.text):
                    try:
                        pil_img = Image.fromarray(img)
                        width, height = pil_img.size
                        pil_img = pil_img.resize((width * 2, height * 2), Image.LANCZOS)

                        # ลองใช้ PSM 6 และ 4 ซึ่งเหมาะกับเอกสารใบเสร็จ
                        for psm in [6, 4]:
                            custom_config = f'--oem 1 --psm {psm}'
                            temp_text = pytesseract.image_to_string(pil_img, lang='tha+eng', config=custom_config)
                            if self._has_useful_data(temp_text):
                                self.text = temp_text
                                break
                    except Exception as e:
                        current_app.logger.warning(f"Error processing image type {img_type}: {e}")

            # บันทึกผลการประมวลลงไฟล์เพื่อการตรวจสอบ (เฉพาะโหมดพัฒนา)
            if current_app.debug:
                log_dir = os.path.join(current_app.root_path, 'logs')
                os.makedirs(log_dir, exist_ok=True)
                log_file = os.path.join(log_dir, f'ocr_result_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')
                with open(log_file, 'w', encoding='utf-8') as f:
                    f.write(self.text)

            return self.text

        except Exception as e:
            current_app.logger.error(f"Error in OCR process: {str(e)}")
            return None

    def _has_useful_data(self, text):
        """ตรวจสอบว่าข้อความที่ได้มีข้อมูลที่เป็นประโยชน์หรือไม่"""
        if not text or len(text.strip()) < 20:  # ข้อความสั้นเกินไป
            return False

        # ตรวจสอบว่ามีคำสำคัญที่พบในใบเสร็จหรือไม่
        keywords = ['บาท', 'รวม', 'ราคา', 'ใบเสร็จ', 'วันที่', 'จำนวน', 'เงินสด', 'THB', 'TOTAL', 'CASH']
        return any(keyword in text for keyword in keywords)

    def extract_date(self):
        """ดึงวันที่จากข้อความใบเสร็จ รองรับรูปแบบวันที่ภาษาไทย"""
        if not self.text:
            self.perform_ocr()

        # รูปแบบวันที่ไทยและสากล
        date_patterns = [
            # รูปแบบสากล DD/MM/YYYY หรือ DD-MM-YYYY
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{4})',

            # รูปแบบไทยแบบแสดงชื่อเดือน DD เดือนไทย YYYY
            r'(\d{1,2}\s+(?:ม\.?ค\.?|ก\.?พ\.?|มี\.?ค\.?|เม\.?ย\.?|พ\.?ค\.?|มิ\.?ย\.?|ก\.?ค\.?|ส\.?ค\.?|ก\.?ย\.?|ต\.?ค\.?|พ\.?ย\.?|ธ\.?ค\.?)\s+\d{4})',

            # รูปแบบไทยแบบมีคำว่า "วันที่" นำหน้า
            r'(?:วันที่|วันที่:)\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',

            # รูปแบบภาษาอังกฤษ
            r'(?:Date|DATE):?\s*(\d{1,2}[/-]\d{1,2}[/-]\d{4})',

            # รูปแบบ DD/MM/YY (ปี 2 หลัก)
            r'(\d{1,2}[/-]\d{1,2}[/-]\d{2})',

            # รูปแบบ "DD MMM YYYY" เช่น 10 Jan 2023
            r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})'
        ]

        for pattern in date_patterns:
            matches = re.search(pattern, self.text)
            if matches:
                date_str = matches.group(1)

                # แปลงเป็นรูปแบบวันที่มาตรฐาน (YYYY-MM-DD)
                try:
                    # แปลงปี พ.ศ. เป็น ค.ศ. ถ้าจำเป็น
                    if re.search(r'\d{4}', date_str) and int(re.search(r'\d{4}', date_str).group(0)) > 2500:
                        date_str = re.sub(r'(\d{1,2}[/-]\d{1,2}[/-])(\d{4})',
                                          lambda m: m.group(1) + str(int(m.group(2)) - 543),
                                          date_str)

                    # ลองแปลงรูปแบบวันที่ต่างๆ
                    formats = ['%d/%m/%Y', '%d-%m-%Y', '%d %b %Y', '%d %B %Y', '%d/%m/%y', '%d-%m-%y']
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
        """ดึงจำนวนเงินรวมจากข้อความใบเสร็จ รองรับรูปแบบไทย"""
        if not self.text:
            self.perform_ocr()

        # รูปแบบจำนวนเงินรวมภาษาไทยและสากล
        amount_patterns = [
            # ภาษาไทย
            r'(?:รวมทั้งสิ้น|รวมเงิน|ยอดรวม|ยอดเงินรวม|รวมสุทธิ|จำนวนเงินรวม|มูลค่ารวม)[^\d\n]*?(\d+(?:[.,]\d{1,2})?)',
            r'(?:จำนวนเงิน|ราคารวม)[^\d\n]*?(\d+(?:[.,]\d{1,2})?)',

            # ภาษาอังกฤษ
            r'(?:TOTAL|GRAND TOTAL|NET AMOUNT|NET|AMOUNT)[^\d\n]*?(\d+(?:[.,]\d{1,2})?)',

            # คำสั้นๆ ที่มักพบในใบเสร็จ ตามด้วยตัวเลข
            r'(?<=TOTAL\s)(\d+(?:[.,]\d{1,2})?)',
            r'(?<=รวม\s)(\d+(?:[.,]\d{1,2})?)',

            # จำนวนเงินที่มี "บาท" ต่อท้าย
            r'(\d+(?:[.,]\d{1,2})?)(?:\s*บาท)',

            # จำนวนเงินพร้อมสัญลักษณ์เงินบาท
            r'฿\s*(\d+(?:[.,]\d{1,2})?)'
        ]

        # ลองค้นหาทุกรูปแบบและเก็บผลลัพธ์ไว้
        all_matches = []
        for pattern in amount_patterns:
            matches = re.finditer(pattern, self.text, re.IGNORECASE)
            for match in matches:
                amount_str = match.group(1).strip()
                try:
                    # ลบตัวอักษรที่ไม่ใช่ตัวเลขและจุดทศนิยม
                    amount_str = re.sub(r'[^\d.]', '', amount_str.replace(',', '.'))
                    amount = float(amount_str)
                    all_matches.append((amount, amount_str))
                except Exception:
                    pass

        # เลือกจำนวนเงินที่มากที่สุด (มักเป็นยอดรวมสุทธิ)
        if all_matches:
            # เรียงตามจำนวนเงินจากมากไปน้อย
            all_matches.sort(reverse=True)
            self.extracted_data['total_amount'] = all_matches[0][0]
            return all_matches[0][0]

        return None

    def extract_vendor(self):
        """ดึงชื่อร้านค้า/ผู้ขายจากข้อความใบเสร็จ รองรับภาษาไทย"""
        if not self.text:
            self.perform_ocr()

        # ชื่อร้านค้ามักจะอยู่ในบรรทัดแรกๆ ของใบเสร็จ
        lines = self.text.split('\n')

        # ตัดบรรทัดว่างออก
        lines = [line.strip() for line in lines if line.strip()]

        if lines:
            # ทดสอบรูปแบบต่างๆ ที่อาจเป็นชื่อร้านค้า

            # 1. ตรวจสอบจากคำที่มักมาก่อนชื่อร้าน
            for line in lines[:5]:  # ดูเฉพาะ 5 บรรทัดแรก
                company_prefixes = ['บริษัท', 'ห้างหุ้นส่วน', 'ร้าน']
                for prefix in company_prefixes:
                    if prefix in line:
                        self.extracted_data['vendor'] = line
                        return line

            # 2. ใช้บรรทัดแรกหรือบรรทัดที่สองเป็นชื่อร้านค้า
            vendor = lines[0]

            # ตรวจสอบว่าบรรทัดแรกเป็นชื่อร้านค้าจริงๆ (ไม่ใช่คำเช่น "ใบเสร็จรับเงิน")
            excluded_words = ['ใบเสร็จ', 'ใบกำกับ', 'ใบเสร็จรับเงิน', 'RECEIPT', 'INVOICE', 'TAX INVOICE']
            if any(word in vendor for word in excluded_words) and len(lines) > 1:
                vendor = lines[1]

                # ถ้าบรรทัดที่ 2 ก็ยังมีคำที่ไม่ใช่ชื่อร้าน ให้ใช้บรรทัดที่ 3
                if any(word in vendor for word in excluded_words) and len(lines) > 2:
                    vendor = lines[2]

            self.extracted_data['vendor'] = vendor
            return vendor

        return None

    def extract_receipt_number(self):
        """ดึงเลขที่ใบเสร็จจากข้อความ"""
        if not self.text:
            self.perform_ocr()

        # รูปแบบเลขที่ใบเสร็จทั่วไป
        receipt_patterns = [
            r'(?:เลขที่|NO|No|no|เลขที่ใบเสร็จ|ใบเสร็จเลขที่|ใบกำกับเลขที่|Receipt No)[\.:\s]*([A-Za-z0-9\-_\/]+)',
            r'(?:ใบเสร็จรับเงิน|ใบกำกับภาษี)[^\n]*?(?:เลขที่|NO|No|no)[\.:\s]*([A-Za-z0-9\-_\/]+)'
        ]

        for pattern in receipt_patterns:
            matches = re.search(pattern, self.text)
            if matches:
                receipt_no = matches.group(1).strip()
                self.extracted_data['receipt_no'] = receipt_no
                return receipt_no

        return None

    def extract_all_data(self):
        """ดึงข้อมูลทั้งหมดจากใบเสร็จ"""
        if not self.text:
            self.perform_ocr()

        self.extract_date()
        self.extract_total_amount()
        self.extract_vendor()
        self.extract_receipt_number()

        return self.extracted_data


def process_receipt_image(image_path):
    """
    ฟังก์ชันหลักสำหรับประมวลผลภาพใบเสร็จและดึงข้อมูล รองรับภาษาไทย

    Args:
        image_path (str): พาธของไฟล์ภาพใบเสร็จ

    Returns:
        dict: ข้อมูลที่ดึงได้จากใบเสร็จ
    """
    receipt_ocr = ReceiptOCR(image_path)
    receipt_ocr.preprocess_image()
    receipt_ocr.perform_ocr()
    extracted_data = receipt_ocr.extract_all_data()

    # ในกรณีที่ไม่มีข้อมูลใดๆ ให้ส่งข้อความแจ้งเตือน
    if all(value is None for value in extracted_data.values()):
        current_app.logger.warning(f"No data extracted from receipt: {image_path}")

    return extracted_data