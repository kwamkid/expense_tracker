# app/forms/account.py
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, BooleanField, SubmitField
from wtforms.validators import DataRequired, ValidationError, Length
from app.models import Account
from flask_login import current_user


class AccountForm(FlaskForm):
    name = StringField('ชื่อบัญชี', validators=[DataRequired(), Length(max=100)])
    balance = FloatField('ยอดเงินคงเหลือ', validators=[DataRequired()])
    is_active = BooleanField('เปิดใช้งาน', default=True)
    submit = SubmitField('บันทึก')

    def validate_name(self, name):
        # ตรวจสอบเฉพาะในโหมดสร้างใหม่ (ไม่มี id)
        if not hasattr(self, 'id') or not self.id.data:
            account = Account.query.filter_by(name=name.data, user_id=current_user.id).first()
            if account:
                raise ValidationError('คุณมีบัญชีชื่อนี้อยู่แล้ว กรุณาใช้ชื่อบัญชีอื่น')