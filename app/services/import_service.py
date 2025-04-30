# app/services/import_service.py
import os
import pandas as pd
import hashlib
import uuid
from datetime import datetime, date, timedelta
from werkzeug.utils import secure_filename
from app.extensions import db
from app.models.transaction import Transaction
from app.models.category_matching import ImportBatch, TransactionCategoryHistory, CategoryKeyword
from app.models.category import Category
from app.models.account import Account


class ImportService:
    """บริการสำหรับการนำเข้าไฟล์ธุรกรรมจากธนาคาร"""

    @staticmethod
    def generate_batch_reference():
        """สร้างรหัสอ้างอิงสำหรับชุดการนำเข้า"""
        return f"IMPORT-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:8]}"

    @staticmethod
    def create_import_batch(file_name, source, organization_id, user_id):
        """สร้างรายการ ImportBatch ใหม่"""
        batch_reference = ImportService.generate_batch_reference()

        import_batch = ImportBatch(
            batch_reference=batch_reference,
            source=source,
            file_name=file_name,
            organization_id=organization_id,
            imported_by=user_id,
            status='pending'
        )

        db.session.add(import_batch)
        db.session.commit()

        return import_batch

    @staticmethod
    def update_batch_status(batch_reference, status, **stats):
        """อัปเดตสถานะและสถิติของ ImportBatch"""
        batch = ImportBatch.query.filter_by(batch_reference=batch_reference).first()
        if not batch:
            return False

        batch.status = status

        # อัปเดตสถิติถ้ามี
        if 'total_records' in stats:
            batch.total_records = stats['total_records']
        if 'imported_records' in stats:
            batch.imported_records = stats['imported_records']
        if 'duplicate_records' in stats:
            batch.duplicate_records = stats['duplicate_records']
        if 'error_records' in stats:
            batch.error_records = stats['error_records']

        if status == 'completed':
            batch.completed_at = datetime.utcnow()

        db.session.commit()
        return True

    @staticmethod
    def generate_transaction_hash(date, amount, description, bank_reference=None):
        """สร้าง hash เพื่อใช้ในการตรวจสอบรายการซ้ำ"""
        # รวมข้อมูลสำคัญของธุรกรรมเพื่อสร้าง hash
        data = f"{date}{amount}{description or ''}{bank_reference or ''}"
        return hashlib.sha256(data.encode()).hexdigest()

    @staticmethod
    def check_duplicate_transaction(transaction_hash, organization_id):
        """ตรวจสอบว่ามีธุรกรรมซ้ำหรือไม่ โดยใช้ transaction_hash"""
        return Transaction.find_duplicate_by_hash(transaction_hash, organization_id)

    @staticmethod
    def find_potential_duplicates(date, amount, organization_id, description=None):
        """ค้นหาธุรกรรมที่อาจซ้ำโดยใช้วันที่และจำนวนเงิน"""
        return Transaction.find_potential_duplicates(date, amount, organization_id, description)

    @staticmethod
    def suggest_category_for_transaction(description, amount, bank_reference, organization_id):
        """เสนอหมวดหมู่ที่เหมาะสมสำหรับธุรกรรมโดยใช้หลายวิธี"""
        # 1. ลองหาจากประวัติการจับคู่ก่อน
        category_id = TransactionCategoryHistory.find_matching_category(
            description, bank_reference, organization_id
        )
        if category_id:
            return category_id

        # 2. ถ้าไม่มีประวัติ ลองหาจากคำสำคัญ
        if description:
            # ดึงคำสำคัญทั้งหมดของ organization นี้ โดยเรียงตาม priority
            keywords = CategoryKeyword.query.filter_by(
                organization_id=organization_id
            ).order_by(CategoryKeyword.priority.desc()).all()

            for keyword in keywords:
                if keyword.is_regex:
                    import re
                    # ใช้ regex ตรวจสอบ
                    if re.search(keyword.pattern, description, re.IGNORECASE):
                        return keyword.category_id
                else:
                    # ใช้การตรวจสอบคำปกติ (case insensitive)
                    if keyword.keyword.lower() in description.lower():
                        return keyword.category_id

        # 3. ตรวจสอบประเภทธุรกรรม (รายรับ/รายจ่าย) และเลือกหมวดหมู่ทั่วไป
        transaction_type = 'income' if amount > 0 else 'expense'

        # ดึงหมวดหมู่ทั่วไปตามประเภทธุรกรรม
        default_category = Category.query.filter_by(
            organization_id=organization_id,
            type=transaction_type,
            name='อื่นๆ'  # ชื่อหมวดหมู่ทั่วไป (อาจต้องปรับตามระบบ)
        ).first()

        return default_category.id if default_category else None

    @staticmethod
    def excel_date_to_datetime(excel_date):
        """
        แปลงวันที่ในรูปแบบ Excel เป็น date object ของ Python

        Excel มีรูปแบบวันที่เป็นจำนวนวันนับจากวันที่ 0 (ซึ่งแตกต่างกันระหว่าง Windows และ Mac)
        - Windows: วันที่ 0 คือ 30/12/1899 (Excel นับ 1/1/1900 เป็นวันที่ 1)
        - Mac: วันที่ 0 คือ 1/1/1904

        ฟังก์ชันนี้จะตรวจสอบและแปลงให้ถูกต้องตามรูปแบบ
        """
        try:
            # ตรวจสอบรูปแบบข้อมูลนำเข้า
            if not isinstance(excel_date, (int, float)):
                raise TypeError("excel_date ต้องเป็น int หรือ float")

            # แก้ไขปัญหาสำหรับ Excel บน Windows ที่มีบัค leap year 1900
            # Excel บน Windows เข้าใจผิดว่าปี 1900 เป็น leap year
            if excel_date > 60 and excel_date < 61:
                # วันที่ 29/2/1900 (ซึ่งไม่มีอยู่จริง)
                raise ValueError("ไม่สามารถแปลงวันที่ 29/2/1900 ได้ (เป็นวันที่ไม่มีอยู่จริง)")

            # ตรวจสอบว่าเป็นวันที่ในรูปแบบ Windows หรือ Mac
            # วันที่ใน Excel สำหรับวันที่ 1/1/2000 อยู่ที่ประมาณ 36500 (Windows) หรือ 35000 (Mac)
            # เราจะใช้เกณฑ์นี้ในการตัดสินใจว่าควรใช้ epoch แบบใด
            if excel_date > 35000:
                # ใช้ epoch แบบ Windows (30/12/1899)
                # แก้ไขปัญหา leap year 1900 ที่ไม่มีอยู่จริง
                if excel_date > 60:
                    excel_date -= 1  # ลบ 1 วันสำหรับวันที่หลังจาก 28/2/1900

                excel_epoch = datetime(1899, 12, 30)
            else:
                # ใช้ epoch แบบ Mac (1/1/1904)
                excel_epoch = datetime(1904, 1, 1)

            # แปลงเป็นวันที่โดยการบวกจำนวนวัน
            days_part = int(excel_date)
            time_part = excel_date - days_part  # เศษที่เหลือคือส่วนของเวลา

            # สร้าง datetime และแปลงเป็น date
            result_date = (excel_epoch + timedelta(days=days_part, seconds=time_part * 86400)).date()
            return result_date

        except (ValueError, TypeError) as e:
            print(f"เกิดข้อผิดพลาดในการแปลงวันที่ Excel: {str(e)}")
            # คืนค่าเป็นวันที่ปัจจุบันหากเกิดข้อผิดพลาด
            return date.today()

    @classmethod
    def find_matching_account(cls, account_number, organization_id):
        """ค้นหาบัญชีที่มีเลขที่บัญชีตรงกับที่ระบุ"""
        # ค้นหาบัญชีที่มีเลขที่บัญชีตรงกัน
        account = Account.query.filter_by(
            account_number=account_number,
            organization_id=organization_id,
            is_active=True
        ).first()

        return account

    @classmethod
    def parse_scb_excel(cls, file_path, organization_id):
        """แปลงไฟล์ Excel จาก SCB เป็นข้อมูลธุรกรรม"""
        try:
            # อ่านไฟล์ Excel
            df = pd.read_excel(file_path)

            # แสดงข้อมูลเบื้องต้นของไฟล์เพื่อตรวจสอบ
            print("ข้อมูลคอลัมน์ในไฟล์:")
            print(df.columns.tolist())
            print("\nตัวอย่างข้อมูล:")
            print(df.head(3))
            print("\nประเภทข้อมูลของแต่ละคอลัมน์:")
            print(df.dtypes)

            # ตรวจสอบรูปแบบของไฟล์ (ต้องมีคอลัมน์ที่จำเป็น)
            required_columns = ['Date', 'Withdrawal', 'Deposit', 'Note', 'Account Number']
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                return {
                    'success': False,
                    'error': f"ไฟล์ Excel ไม่ถูกต้อง ไม่พบคอลัมน์: {', '.join(missing_columns)}"
                }

            # เตรียมข้อมูลธุรกรรม
            transactions = []

            for _, row in df.iterrows():
                # แปลงวันที่ให้เป็นรูปแบบที่ถูกต้อง
                try:
                    # แสดงข้อมูลเพื่อตรวจสอบ
                    print(f"กำลังแปลงวันที่: {row['Date']} ประเภท: {type(row['Date'])}")

                    # ตรวจสอบประเภทข้อมูลและแปลงให้เป็นวันที่
                    if isinstance(row['Date'], str):
                        # ถ้าเป็น string พยายามแปลงเป็นวันที่
                        try:
                            transaction_date = datetime.strptime(row['Date'], '%d/%m/%Y').date()
                        except ValueError:
                            # ลองรูปแบบอื่นๆ
                            date_formats = ['%Y-%m-%d', '%d-%m-%Y', '%m/%d/%Y', '%d.%m.%Y']
                            for fmt in date_formats:
                                try:
                                    transaction_date = datetime.strptime(row['Date'], fmt).date()
                                    break
                                except ValueError:
                                    continue
                            else:  # ถ้าไม่มีรูปแบบใดตรงเลย
                                print(f"ไม่สามารถแปลงวันที่ '{row['Date']}' ได้ ใช้วันที่ปัจจุบันแทน")
                                transaction_date = date.today()

                    elif isinstance(row['Date'], datetime):
                        # ถ้าเป็น datetime object
                        transaction_date = row['Date'].date()

                    elif isinstance(row['Date'], pd.Timestamp):
                        # ถ้าเป็น pandas Timestamp
                        transaction_date = row['Date'].date()

                    elif pd.isna(row['Date']):
                        # ถ้าเป็นค่าว่าง ข้ามรายการนี้
                        print("พบค่าว่างในคอลัมน์วันที่ ข้ามรายการนี้")
                        continue

                    elif isinstance(row['Date'], (int, float)):
                        # ถ้าเป็นตัวเลข (Excel เก็บวันที่เป็นจำนวนวันนับจากวันที่กำหนด)
                        transaction_date = cls.excel_date_to_datetime(row['Date'])

                    else:
                        # ถ้าเป็นประเภทอื่นที่ไม่รองรับ ข้ามรายการนี้
                        print(f"ไม่รองรับประเภทข้อมูลวันที่ {type(row['Date'])}")
                        continue

                    # แสดงผลหลังการแปลง
                    print(f"แปลงเป็นวันที่: {transaction_date}")

                except Exception as e:
                    # ถ้าแปลงวันที่ไม่ได้ ข้ามรายการนี้
                    print(f"เกิดข้อผิดพลาดในการแปลงวันที่: {str(e)}")
                    continue

                # กำหนดประเภทและจำนวนเงิน
                withdrawal = row['Withdrawal'] if not pd.isna(row['Withdrawal']) else 0
                deposit = row['Deposit'] if not pd.isna(row['Deposit']) else 0

                if withdrawal > 0 and deposit > 0:
                    # ไม่ควรมีทั้งถอนและฝากในรายการเดียวกัน แต่ถ้ามีให้ใช้ยอดสุทธิ
                    amount = deposit - withdrawal
                elif withdrawal > 0:
                    amount = -withdrawal  # ถอนเงิน (ติดลบ)
                elif deposit > 0:
                    amount = deposit  # ฝากเงิน (บวก)
                else:
                    # ไม่มีการเคลื่อนไหวของเงิน ให้ข้ามรายการนี้
                    continue

                # กำหนดประเภทธุรกรรม
                transaction_type = 'income' if amount > 0 else 'expense'

                # รายละเอียดธุรกรรม
                description = str(row['Note']) if not pd.isna(row['Note']) else None

                # เลขที่บัญชี
                account_number = str(row['Account Number']) if not pd.isna(row['Account Number']) else None

                # ค้นหาบัญชีที่ตรงกับเลขที่บัญชี
                matching_account = None
                if account_number:
                    matching_account = cls.find_matching_account(account_number, organization_id)

                # รหัสอ้างอิงธนาคาร (ถ้ามี)
                bank_reference = None
                if 'Reference' in df.columns and not pd.isna(row['Reference']):
                    bank_reference = str(row['Reference'])

                # สร้าง hash สำหรับตรวจสอบรายการซ้ำ
                transaction_hash = cls.generate_transaction_hash(
                    transaction_date.strftime('%Y-%m-%d'),
                    amount,
                    description,
                    bank_reference
                )

                # เสนอหมวดหมู่ที่เหมาะสม
                suggested_category_id = cls.suggest_category_for_transaction(
                    description, amount, bank_reference, organization_id
                )

                # รวมข้อมูลธุรกรรม
                transactions.append({
                    'transaction_date': transaction_date,
                    'amount': abs(amount),  # เก็บเป็นค่าบวกเสมอ
                    'type': transaction_type,
                    'description': description,
                    'bank_reference': bank_reference,
                    'transaction_hash': transaction_hash,
                    'suggested_category_id': suggested_category_id,
                    'account_number': account_number,
                    'matching_account_id': matching_account.id if matching_account else None,
                    'matching_account_name': matching_account.name if matching_account else None
                })

            return {
                'success': True,
                'transactions': transactions
            }

        except Exception as e:
            import traceback
            return {
                'success': False,
                'error': f"เกิดข้อผิดพลาดในการอ่านไฟล์: {str(e)}",
                'traceback': traceback.format_exc()
            }

    @classmethod
    def save_transactions(cls, transactions_data, account_id, batch_reference, organization_id, user_id):
        """บันทึกธุรกรรมลงในฐานข้อมูล"""
        stats = {
            'total_records': len(transactions_data),
            'imported_records': 0,
            'duplicate_records': 0,
            'error_records': 0
        }

        # ดึงบัญชีที่จะเพิ่มธุรกรรม
        account = Account.query.get(account_id)
        if not account:
            return {
                'success': False,
                'error': "ไม่พบบัญชีที่ระบุ"
            }

        for data in transactions_data:
            try:
                # ตรวจสอบรายการซ้ำโดยใช้ transaction_hash
                duplicate = cls.check_duplicate_transaction(data['transaction_hash'], organization_id)
                if duplicate:
                    stats['duplicate_records'] += 1
                    continue

                # สร้างธุรกรรมใหม่
                transaction = Transaction(
                    amount=data['amount'],
                    description=data['description'],
                    transaction_date=data['transaction_date'],
                    type=data['type'],
                    status='completed',  # ธุรกรรมจากธนาคารถือว่าเสร็จสิ้นแล้ว
                    organization_id=organization_id,
                    account_id=account_id,
                    category_id=data['category_id'],
                    transaction_hash=data['transaction_hash'],
                    bank_reference=data['bank_reference'],
                    imported_from='SCB',
                    import_batch_id=batch_reference,
                    created_by=user_id,
                    updated_by=user_id
                )

                db.session.add(transaction)

                # อัปเดตยอดเงินในบัญชี
                if data['type'] == 'income':
                    account.balance += data['amount']
                else:
                    account.balance -= data['amount']

                # อัปเดตประวัติการจับคู่หมวดหมู่
                if data['description']:
                    TransactionCategoryHistory.update_history(
                        data['description'],
                        data['bank_reference'],
                        data['category_id'],
                        organization_id
                    )

                stats['imported_records'] += 1

            except Exception as e:
                stats['error_records'] += 1
                # อาจเก็บ log หรือรายงานข้อผิดพลาด
                continue

        # บันทึกข้อมูลลงฐานข้อมูล
        try:
            db.session.commit()
            # อัปเดตสถานะการนำเข้า
            cls.update_batch_status(batch_reference, 'completed', **stats)

            return {
                'success': True,
                'stats': stats
            }
        except Exception as e:
            db.session.rollback()
            # อัปเดตสถานะการนำเข้าเป็นล้มเหลว
            cls.update_batch_status(batch_reference, 'failed')

            return {
                'success': False,
                'error': f"เกิดข้อผิดพลาดในการบันทึกข้อมูล: {str(e)}",
                'stats': stats
            }

    @classmethod
    def save_transactions_multi_accounts(cls, transactions_data, batch_reference, organization_id, user_id):
        """บันทึกธุรกรรมลงในฐานข้อมูล รองรับการบันทึกลงหลายบัญชี"""
        stats = {
            'total_records': len(transactions_data),
            'imported_records': 0,
            'duplicate_records': 0,
            'error_records': 0
        }

        # จัดกลุ่มธุรกรรมตามบัญชี
        account_transactions = {}
        for data in transactions_data:
            account_id = data['selected_account_id']
            if account_id not in account_transactions:
                account_transactions[account_id] = []
            account_transactions[account_id].append(data)

        # ตรวจสอบว่ามีบัญชีทั้งหมดที่ต้องการจะบันทึกหรือไม่
        accounts = {}
        for account_id in account_transactions.keys():
            account = Account.query.get(account_id)
            if not account:
                return {
                    'success': False,
                    'error': f"ไม่พบบัญชีที่ระบุ (ID: {account_id})"
                }
            accounts[account_id] = account

        try:
            # ประมวลผลธุรกรรมทั้งหมด
            for account_id, transactions in account_transactions.items():
                account = accounts[account_id]

                for data in transactions:
                    try:
                        # ตรวจสอบรายการซ้ำโดยใช้ transaction_hash
                        duplicate = cls.check_duplicate_transaction(data['transaction_hash'], organization_id)
                        if duplicate:
                            stats['duplicate_records'] += 1
                            continue

                        # สร้างธุรกรรมใหม่
                        transaction = Transaction(
                            amount=data['amount'],
                            description=data['description'],
                            transaction_date=data['transaction_date'],
                            type=data['type'],
                            status='completed',  # ธุรกรรมจากธนาคารถือว่าเสร็จสิ้นแล้ว
                            organization_id=organization_id,
                            account_id=account_id,
                            category_id=data['category_id'],
                            transaction_hash=data['transaction_hash'],
                            bank_reference=data.get('bank_reference'),
                            imported_from='SCB',
                            import_batch_id=batch_reference,
                            created_by=user_id,
                            updated_by=user_id
                        )

                        db.session.add(transaction)

                        # อัปเดตยอดเงินในบัญชี
                        if data['type'] == 'income':
                            account.balance += data['amount']
                        else:
                            account.balance -= data['amount']

                        # อัปเดตประวัติการจับคู่หมวดหมู่
                        if data['description']:
                            TransactionCategoryHistory.update_history(
                                data['description'],
                                data.get('bank_reference'),
                                data['category_id'],
                                organization_id
                            )

                        stats['imported_records'] += 1

                    except Exception as e:
                        stats['error_records'] += 1
                        # ไม่ต้อง raise exception ให้ข้ามไปรายการต่อไป
                        continue

            # บันทึกข้อมูลลงฐานข้อมูล
            db.session.commit()

            # อัปเดตสถานะการนำเข้า
            cls.update_batch_status(batch_reference, 'completed', **stats)

            return {
                'success': True,
                'stats': stats
            }
        except Exception as e:
            db.session.rollback()
            # อัปเดตสถานะการนำเข้าเป็นล้มเหลว
            cls.update_batch_status(batch_reference, 'failed')

            return {
                'success': False,
                'error': f"เกิดข้อผิดพลาดในการบันทึกข้อมูล: {str(e)}",
                'stats': stats
            }