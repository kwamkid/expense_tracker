from app.models import db, Transaction, BankAccount
from datetime import datetime
import pytz

bangkok_tz = pytz.timezone('Asia/Bangkok')


class BalanceService:
    @staticmethod
    def update_bank_balance(bank_account_id):
        """อัพเดทยอดคงเหลือของบัญชีธนาคาร"""
        bank_account = BankAccount.query.get(bank_account_id)
        if not bank_account:
            return False

        # คำนวณยอดรวมจาก transaction ที่ completed
        completed_transactions = Transaction.query.filter_by(
            bank_account_id=bank_account_id,
            status='completed'
        ).all()

        total_income = sum(t.amount for t in completed_transactions if t.type == 'income')
        total_expense = sum(t.amount for t in completed_transactions if t.type == 'expense')

        bank_account.current_balance = bank_account.initial_balance + total_income - total_expense
        db.session.commit()

        return True

    @staticmethod
    def update_transaction_status(transaction_id, new_status):
        """อัพเดทสถานะของ transaction และคำนวณยอดคงเหลือใหม่"""
        transaction = Transaction.query.get(transaction_id)
        if not transaction:
            return False

        old_status = transaction.status
        transaction.status = new_status

        # ถ้าเปลี่ยนเป็น completed ให้บันทึกวันที่ completed
        if new_status == 'completed' and old_status != 'completed':
            transaction.completed_date = datetime.now(bangkok_tz)

        db.session.commit()

        # อัพเดทยอดคงเหลือถ้ามีการเปลี่ยนสถานะเกี่ยวกับ completed
        if transaction.bank_account_id and (old_status == 'completed' or new_status == 'completed'):
            BalanceService.update_bank_balance(transaction.bank_account_id)

        return True

    @staticmethod
    def recalculate_all_balances(user_id):
        """คำนวณยอดคงเหลือใหม่ทั้งหมดสำหรับผู้ใช้"""
        bank_accounts = BankAccount.query.filter_by(user_id=user_id).all()

        for account in bank_accounts:
            BalanceService.update_bank_balance(account.id)

        return True