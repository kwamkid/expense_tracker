# app/forms/transaction.py
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, FloatField, SelectField, DateField, TextAreaField, SubmitField
from wtforms.validators import DataRequired, Optional, ValidationError
from datetime import date


class TransactionForm(FlaskForm):
    amount = FloatField('จำนวนเงิน', validators=[DataRequired()])
    description = TextAreaField('รายละเอียด', validators=[Optional()])
    transaction_date = DateField('วันที่', validators=[DataRequired()], default=date.today)

    type = SelectField(
        'ประเภท',
        choices=[('income', 'รายรับ'), ('expense', 'รายจ่าย')],
        validators=[DataRequired()]
    )

    status = SelectField(
        'สถานะ',
        choices=[('completed', 'เสร็จสิ้น'), ('pending', 'รอดำเนินการ')],
        validators=[DataRequired()],
        default='completed'
    )

    account_id = SelectField('บัญชี', coerce=int, validators=[DataRequired()])
    category_id = SelectField('หมวดหมู่', coerce=int, validators=[DataRequired()])

    receipt = FileField('ใบเสร็จ', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif', 'pdf'], 'อนุญาตเฉพาะไฟล์รูปภาพหรือ PDF เท่านั้น')
    ])

    submit = SubmitField('บันทึก')

    def validate_amount(self, amount):
        if amount.data <= 0:
            raise ValidationError('จำนวนเงินต้องมากกว่า 0')