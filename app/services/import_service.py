# app/services/import_service.py
import pandas as pd
from datetime import datetime
import re


class BankImportService:
    def __init__(self, bank_type):
        self.bank_type = bank_type
        self.parsers = {
            'scb': self._parse_scb,
            'kbank': self._parse_kbank,
            'bangkok': self._parse_bangkok,
            'krungsri': self._parse_krungsri
        }

    def parse_file(self, filepath):
        if self.bank_type not in self.parsers:
            raise ValueError(f"ไม่รองรับธนาคาร {self.bank_type}")

        parser = self.parsers[self.bank_type]
        return parser(filepath)

    def _parse_scb(self, filepath):
        """Parse SCB Excel file - รองรับโครงสร้างไฟล์ SCB จริง"""
        try:
            # อ่านไฟล์ Excel
            df = pd.read_excel(filepath)

            # แสดงชื่อคอลัมน์ทั้งหมดเพื่อ debug
            print(f"Columns found: {df.columns.tolist()}")

            # หาคอลัมน์ที่ตรงกัน (case-insensitive)
            column_map = {}
            for col in df.columns:
                col_lower = col.lower()
                if 'account number' in col_lower or 'เลขบัญชี' in col_lower:
                    column_map['account_number'] = col
                elif 'account name' in col_lower or 'ชื่อบัญชี' in col_lower:
                    column_map['account_name'] = col
                elif 'date' in col_lower or 'วันที่' in col_lower:
                    column_map['date'] = col
                elif 'time' in col_lower or 'เวลา' in col_lower:
                    column_map['time'] = col
                elif 'withdrawal' in col_lower or 'ถอน' in col_lower:
                    column_map['withdrawal'] = col
                elif 'deposit' in col_lower or 'เงินเข้า' in col_lower or 'ฝาก' in col_lower:
                    column_map['deposit'] = col
                elif 'description' in col_lower or 'รายละเอียด' in col_lower:
                    column_map['description'] = col
                elif 'note' in col_lower or 'โน๊ต' in col_lower or 'หมายเหตุ' in col_lower:
                    column_map['note'] = col

            # ตรวจสอบว่ามีคอลัมน์ที่จำเป็น
            required_columns = ['date', 'withdrawal', 'deposit']
            missing_columns = []
            for req_col in required_columns:
                if req_col not in column_map:
                    missing_columns.append(req_col)

            if missing_columns:
                raise ValueError(f"ไม่พบคอลัมน์ที่จำเป็น: {', '.join(missing_columns)}")

            transactions = []
            for index, row in df.iterrows():
                # แปลงวันที่
                try:
                    if pd.isna(row[column_map['date']]):
                        continue

                    # ตรวจสอบประเภทของวันที่
                    date_value = row[column_map['date']]

                    if isinstance(date_value, str):
                        # พยายามแปลงวันที่จาก string
                        try:
                            transaction_date = datetime.strptime(date_value, '%d/%m/%Y').date()
                        except ValueError:
                            try:
                                transaction_date = datetime.strptime(date_value, '%Y-%m-%d').date()
                            except ValueError:
                                continue
                    elif isinstance(date_value, (datetime, pd.Timestamp)):
                        transaction_date = date_value.date()
                    else:
                        continue

                except Exception as e:
                    print(f"Error parsing date on row {index}: {e}")
                    continue

                # ดึงข้อมูลการเงิน
                withdrawal = 0
                deposit = 0

                # จัดการ withdrawal
                if 'withdrawal' in column_map and not pd.isna(row[column_map['withdrawal']]):
                    try:
                        withdrawal = float(str(row[column_map['withdrawal']]).replace(',', ''))
                    except:
                        withdrawal = 0

                # จัดการ deposit
                if 'deposit' in column_map and not pd.isna(row[column_map['deposit']]):
                    try:
                        deposit = float(str(row[column_map['deposit']]).replace(',', ''))
                    except:
                        deposit = 0

                # ถ้าไม่มียอดเงินเข้าหรือออก ข้ามรายการนี้
                if withdrawal == 0 and deposit == 0:
                    continue

                # กำหนดประเภทรายการ
                if withdrawal > 0:
                    amount = withdrawal
                    trans_type = 'expense'
                else:
                    amount = deposit
                    trans_type = 'income'

                # ดึงข้อมูลอื่นๆ
                description = ''
                if 'description' in column_map and not pd.isna(row[column_map['description']]):
                    description = str(row[column_map['description']])

                note = ''
                if 'note' in column_map and not pd.isna(row[column_map['note']]):
                    note = str(row[column_map['note']])

                # รวม description และ note ถ้ามี
                full_description = description
                if note:
                    full_description = f"{description} ({note})" if description else note

                time_str = ''
                if 'time' in column_map and not pd.isna(row[column_map['time']]):
                    time_str = str(row[column_map['time']])

                account_number = ''
                if 'account_number' in column_map and not pd.isna(row[column_map['account_number']]):
                    account_number = str(row[column_map['account_number']])

                # สร้างรายการ transaction
                transactions.append({
                    'index': index,
                    'date': transaction_date,
                    'amount': amount,
                    'type': trans_type,
                    'description': full_description,
                    'reference': f"{time_str}",  # ใช้เวลาเป็น reference
                    'account_number': account_number
                })

            if not transactions:
                raise ValueError("ไม่พบรายการธุรกรรมในไฟล์")

            return transactions

        except Exception as e:
            import traceback
            print(f"Error parsing SCB file: {str(e)}")
            print(traceback.format_exc())
            raise ValueError(f"เกิดข้อผิดพลาดในการอ่านไฟล์: {str(e)}")

    def _parse_kbank(self, filepath):
        """Parse KBank Excel file"""
        # TODO: Implement KBank parser
        raise NotImplementedError("ยังไม่รองรับการนำเข้าจาก KBank")

    def _parse_bangkok(self, filepath):
        """Parse Bangkok Bank Excel file"""
        # TODO: Implement Bangkok Bank parser
        raise NotImplementedError("ยังไม่รองรับการนำเข้าจาก Bangkok Bank")

    def _parse_krungsri(self, filepath):
        """Parse Krungsri Excel file"""
        # TODO: Implement Krungsri parser
        raise NotImplementedError("ยังไม่รองรับการนำเข้าจาก Krungsri")

    def check_duplicate_transaction(self, user_id, date, amount, description):
        """ตรวจสอบว่ามีรายการซ้ำหรือไม่"""
        from app.models import Transaction

        # ค้นหารายการที่มีวันที่, จำนวนเงิน และรายละเอียดเหมือนกัน
        existing = Transaction.query.filter_by(
            user_id=user_id,
            transaction_date=date,
            amount=amount
        ).all()

        # ตรวจสอบรายละเอียดเพิ่มเติม
        for trans in existing:
            if trans.description == description:
                return True

        return False