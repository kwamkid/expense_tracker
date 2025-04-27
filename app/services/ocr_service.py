import os
import re
import cv2
import numpy as np
import pytesseract
from datetime import datetime
from PIL import Image, ImageEnhance
from flask import current_app
from app.models.ocr_pattern import OCRPattern

# กำหนดตำแหน่งของ Tesseract - ตรวจสอบก่อนว่ามีหรือไม่
if os.path.exists('/opt/homebrew/bin/tesseract'):
    pytesseract.pytesseract.tesseract_cmd = '/opt/homebrew/bin/tesseract'
elif os.path.exists('/usr/bin/tesseract'):
    pytesseract.pytesseract.tesseract_cmd = '/usr/bin/tesseract'
elif os.path.exists('/usr/local/bin/tesseract'):
    pytesseract.pytesseract.tesseract_cmd = '/usr/local/bin/tesseract'


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
        try:
            # อ่านภาพด้วย OpenCV
            image = cv2.imread(self.image_path)

            if image is None:
                current_app.logger.error(f"Failed to read image: {self.image_path}")
                raise ValueError(f"Failed to read image file: {self.image_path}")

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

            current_app.logger.info(f"Image preprocessing successful for {self.image_path}")
            return self.preprocessed_image

        except Exception as e:
            current_app.logger.error(f"Error in image preprocessing: {str(e)}")
            raise

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

            # บันทึกข้อมูลเพื่อการดีบัก
            current_app.logger.info(f"OCR: Processing image with size {width}x{height}")
            current_app.logger.info(f"OCR: Tesseract path: {pytesseract.pytesseract.tesseract_cmd}")

            # ทดลองอ่านด้วยการตั้งค่าที่เหมาะกับใบเสร็จภาษาไทย
            # --oem 1: LSTM OCR Engine (แม่นยำกว่าสำหรับภาษาไทย)
            # --psm 6: Assume a single uniform block of text
            try:
                custom_config = r'--oem 1 --psm 6'
                current_app.logger.info(f"OCR: Attempting OCR with config: {custom_config}")
                self.text = pytesseract.image_to_string(pil_image, lang='tha+eng', config=custom_config)
                current_app.logger.info(f"OCR: First pass result length: {len(self.text) if self.text else 0}")
            except Exception as e:
                current_app.logger.error(f"OCR: Error in first pass: {str(e)}")
                # ลองใช้ oem 0 (เครื่องจักรเก่า) ซึ่งอาจทำงานได้ในบางกรณี
                try:
                    custom_config = r'--oem 0 --psm 6'
                    current_app.logger.info(f"OCR: Trying fallback config: {custom_config}")
                    self.text = pytesseract.image_to_string(pil_image, lang='tha+eng', config=custom_config)
                except Exception as e2:
                    current_app.logger.error(f"OCR: Error in fallback pass: {str(e2)}")
                    self.text = ""

            # หากไม่พบข้อมูล ลองใช้โหมด PSM อื่น
            if not self._has_useful_data(self.text):
                try:
                    # --psm 4: Assume a single column of text of variable sizes
                    custom_config = r'--oem 1 --psm 4'
                    current_app.logger.info(f"OCR: Trying alternate layout: {custom_config}")
                    text2 = pytesseract.image_to_string(pil_image, lang='tha+eng', config=custom_config)
                    if self._has_useful_data(text2):
                        self.text = text2
                        current_app.logger.info("OCR: Alternate layout produced better results")
                except Exception as e:
                    current_app.logger.error(f"OCR: Error in alternate layout: {str(e)}")

            # ลองใช้ภาพที่ผ่านการประมวลผลในแบบอื่นๆ
            for img_type, img in self.multi_processed_images.items():
                if not self._has_useful_data(self.text):
                    try:
                        pil_img = Image.fromarray(img)
                        width, height = pil_img.size
                        pil_img = pil_img.resize((width * 2, height * 2), Image.LANCZOS)

                        current_app.logger.info(f"OCR: Trying image type: {img_type}")
                        # ลองใช้ PSM 6 และ 4 ซึ่งเหมาะกับเอกสารใบเสร็จ
                        for psm in [6, 4]:
                            try:
                                custom_config = f'--oem 1 --psm {psm}'
                                temp_text = pytesseract.image_to_string(pil_img, lang='tha+eng', config=custom_config)
                                if self._has_useful_data(temp_text):
                                    self.text = temp_text
                                    current_app.logger.info(
                                        f"OCR: Image type {img_type} with PSM {psm} produced better results")
                                    break
                            except Exception as e:
                                current_app.logger.warning(f"OCR: Error processing with PSM {psm}: {e}")
                    except Exception as e:
                        current_app.logger.warning(f"OCR: Error processing image type {img_type}: {e}")

            # บันทึกผลการประมวลลงไฟล์เพื่อการตรวจสอบ
            log_dir = os.path.join(current_app.root_path, 'logs')
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, f'ocr_result_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write(self.text if self.text else "No text extracted")
            current_app.logger.info(f"OCR: Results saved to {log_file}")

            return self.text

        except Exception as e:
            current_app.logger.error(f"OCR: Critical error in OCR process: {str(e)}")
            # สร้างไดเรกทอรีเพื่อบันทึกข้อผิดพลาด
            try:
                log_dir = os.path.join(current_app.root_path, 'logs')
                os.makedirs(log_dir, exist_ok=True)
                error_file = os.path.join(log_dir, f'ocr_error_{datetime.now().strftime("%Y%m%d_%H%M%S")}.txt')
                with open(error_file, 'w', encoding='utf-8') as f:
                    f.write(f"OCR Error: {str(e)}")
                current_app.logger.info(f"OCR: Error details saved to {error_file}")
            except:
                pass
            return None

    def _has_useful_data(self, text):
        """ตรวจสอบว่าข้อความที่ได้มีข้อมูลที่เป็นประโยชน์หรือไม่"""
        if not text or len(text.strip()) < 20:  # ข้อความสั้นเกินไป
            return False

        # ตรวจสอบว่ามีคำสำคัญที่พบในใบเสร็จหรือไม่
        keywords = ['บาท', 'รวม', 'ราคา', 'ใบเสร็จ', 'วันที่', 'จำนวน', 'เงินสด', 'THB', 'TOTAL', 'CASH']
        return any(keyword in text for keyword in keywords)

    def extract_using_patterns(self, field_name):
        """ดึงข้อมูลโดยใช้รูปแบบ regex ที่กำหนดไว้ในฐานข้อมูล

        Args:
            field_name (str): ชื่อฟิลด์ที่ต้องการดึง เช่น 'date', 'total_amount'

        Returns:
            any: ข้อมูลที่ดึงได้ หรือ None หากไม่พบ
        """
        if not self.text:
            self.perform_ocr()

        try:
            current_app.logger.info(f"Starting {field_name} extraction from text using database patterns")

            # ดึงรูปแบบทั้งหมดจากฐานข้อมูล
            patterns = OCRPattern.get_patterns_by_name(field_name)

            if not patterns:
                current_app.logger.warning(f"No patterns found for field: {field_name}")

                # ถ้าเป็น total_amount และไม่พบรูปแบบใดๆ ให้ใช้รูปแบบพื้นฐาน
                if field_name == 'total_amount':
                    # รูปแบบสำหรับ "รวมทั้งสิน"
                    current_app.logger.info("Using hardcoded patterns for total_amount as fallback")
                    fallback_patterns = [
                        r'[\'"]?รวมทั้งสิน[\'"]?\s*[\'"]?(\d+(?:[.,]\d{1,2})?)[\'"]?',
                        r'รวมทั้งสิ้น\s*(\d+(?:[.,]\d{1,2})?)',
                        r'จำนวนเงินหลังหักส่วนลด\s*(\d+(?:[.,]\d{1,2})?)',
                        r'TOTAL\s*(\d+(?:[.,]\d{1,2})?)'
                    ]

                    for pattern in fallback_patterns:
                        try:
                            current_app.logger.info(f"Trying fallback pattern: {pattern}")
                            matches = re.search(pattern, self.text)
                            if matches:
                                value = matches.group(1).strip()
                                current_app.logger.info(f"Fallback pattern matched: {value}")

                                # แปลงเป็นตัวเลข
                                clean_value = re.sub(r'[^\d.]', '', value.replace(',', '.'))
                                result = float(clean_value)
                                self.extracted_data[field_name] = result
                                return result
                        except Exception as e:
                            current_app.logger.error(f"Error with fallback pattern: {e}")

                return None

            # ทดลองใช้ทุกรูปแบบตามลำดับความสำคัญ
            for pattern_obj in patterns:
                try:
                    pattern = pattern_obj.pattern
                    current_app.logger.info(f"Trying pattern '{pattern_obj.description}': {pattern}")

                    matches = re.search(pattern, self.text)
                    if matches:
                        # ดึงค่าจากกลุ่มที่ 1 (ส่วนที่ตรงกับ regex ในวงเล็บ)
                        value = matches.group(1).strip()
                        current_app.logger.info(f"Pattern matched: {value}")

                        # แปลงค่าตามชนิดของฟิลด์
                        if field_name == 'date':
                            # แปลงเป็นรูปแบบ YYYY-MM-DD
                            try:
                                # แปลงปี พ.ศ. เป็น ค.ศ. ถ้าจำเป็น
                                if re.search(r'\d{4}', value) and int(re.search(r'\d{4}', value).group(0)) > 2500:
                                    value = re.sub(r'(\d{1,2}[/-]\d{1,2}[/-])(\d{4})',
                                                   lambda m: m.group(1) + str(int(m.group(2)) - 543),
                                                   value)

                                # ลองแปลงรูปแบบวันที่ต่างๆ
                                formats = ['%d/%m/%Y', '%d-%m-%Y', '%d %b %Y', '%d %B %Y', '%d/%m/%y', '%d-%m-%y']
                                for fmt in formats:
                                    try:
                                        date_obj = datetime.strptime(value, fmt)
                                        result = date_obj.strftime('%Y-%m-%d')
                                        self.extracted_data[field_name] = result
                                        return result
                                    except ValueError:
                                        continue
                            except Exception as e:
                                current_app.logger.error(f"Error parsing date: {e}")
                                continue

                        elif field_name == 'total_amount':
                            try:
                                # ลบตัวอักษรที่ไม่ใช่ตัวเลขและจุดทศนิยม
                                clean_value = re.sub(r'[^\d.]', '', value.replace(',', '.'))
                                result = float(clean_value)
                                self.extracted_data[field_name] = result
                                return result
                            except ValueError:
                                current_app.logger.error(f"Could not convert to float: {value}")
                                continue

                        else:
                            # สำหรับฟิลด์อื่นๆ เก็บเป็นสตริง
                            self.extracted_data[field_name] = value
                            return value

                except Exception as e:
                    current_app.logger.error(f"Error applying pattern: {e}")
                    continue

            current_app.logger.warning(f"No pattern matched for field: {field_name}")
            return None

        except Exception as e:
            current_app.logger.error(f"Error in extract_using_patterns for {field_name}: {str(e)}")
            return None

    def extract_date(self):
        """ดึงวันที่จากข้อความใบเสร็จ"""
        return self.extract_using_patterns('date')

    def extract_total_amount(self):
        """ดึงจำนวนเงินรวมจากข้อความใบเสร็จ"""
        return self.extract_using_patterns('total_amount')

    def extract_vendor(self):
        """ดึงชื่อร้านค้า/ผู้ขายจากข้อความใบเสร็จ"""
        return self.extract_using_patterns('vendor')

    def extract_receipt_number(self):
        """ดึงเลขที่ใบเสร็จจากข้อความใบเสร็จ"""
        return self.extract_using_patterns('receipt_number')

    def extract_items(self):
        """ดึงรายการสินค้าจากข้อความใบเสร็จ"""
        items_text = self.extract_using_patterns('items_section')
        if not items_text:
            return []

        # ตัดข้อความเป็นบรรทัด
        lines = items_text.split('\n')
        items = []

        # ใช้ regex ในการแยกข้อมูลสินค้าในแต่ละบรรทัด
        # ตัวอย่าง: "1 สินค้า A 100.00" หรือ "สินค้า B 2 x 50.00 100.00"
        item_pattern = r'(.+?)\s+(\d+(?:[.,]\d{1,2})?)$'  # ชื่อสินค้า ตามด้วยราคา
        for line in lines:
            line = line.strip()
            if not line:
                continue

            match = re.search(item_pattern, line)
            if match:
                name = match.group(1).strip()
                price = float(match.group(2).replace(',', '.'))
                items.append({
                    'name': name,
                    'price': price
                })

        return items

    def extract_all_data(self):
        """ดึงข้อมูลทั้งหมดจากใบเสร็จ"""
        if not self.text:
            self.perform_ocr()

        current_app.logger.info("Extracting all data from receipt")
        current_app.logger.info(f"Full OCR text:\n{self.text}")

        self.extract_date()
        self.extract_total_amount()
        self.extract_vendor()
        self.extract_receipt_number()
        items = self.extract_items()
        if items:
            self.extracted_data['items'] = items

        # ตรวจสอบว่าได้ข้อมูลบ้างหรือไม่
        if all(value is None for value in self.extracted_data.values() if not isinstance(value, list)):
            current_app.logger.warning(f"No data extracted from receipt: {self.image_path}")
        else:
            current_app.logger.info(f"Extracted data: {self.extracted_data}")

        return self.extracted_data


def process_receipt_image(image_path):
    """
    ฟังก์ชันหลักสำหรับประมวลผลภาพใบเสร็จและดึงข้อมูล รองรับภาษาไทย

    Args:
        image_path (str): พาธของไฟล์ภาพใบเสร็จ

    Returns:
        dict: ข้อมูลที่ดึงได้จากใบเสร็จ
    """
    try:
        current_app.logger.info(f"Starting OCR processing for image: {image_path}")

        # ตรวจสอบว่าไฟล์มีอยู่จริง
        if not os.path.exists(image_path):
            current_app.logger.error(f"Image file not found: {image_path}")
            raise FileNotFoundError(f"Image file not found: {image_path}")

        receipt_ocr = ReceiptOCR(image_path)
        receipt_ocr.preprocess_image()
        receipt_ocr.perform_ocr()
        extracted_data = receipt_ocr.extract_all_data()

        return extracted_data

    except Exception as e:
        current_app.logger.error(f"Error in process_receipt_image: {str(e)}")
        # ส่งคืนข้อมูลว่างเปล่าแทนที่จะก่อให้เกิดข้อผิดพลาด
        return {
            'date': None,
            'total_amount': None,
            'vendor': None,
            'items': [],
            'receipt_no': None
        }