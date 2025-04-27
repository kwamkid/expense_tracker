# app/forms/account.py
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, BooleanField, SubmitField, HiddenField
from wtforms.validators import DataRequired, ValidationError, Length
from app.models import Account
from flask_login import current_user


class AccountForm(FlaskForm):
    id = HiddenField('ID')  # เพิ่ม hidden field สำหรับเก็บ ID
    name = StringField('ชื่อบัญชี', validators=[DataRequired(), Length(max=100)])
    balance = FloatField('ยอดเงินคงเหลือ', validators=[DataRequired()])
    is_active = BooleanField('เปิดใช้งาน', default=True)
    submit = SubmitField('บันทึก')

    def validate_name(self, name):
        # ตรวจสอบชื่อซ้ำโดยคำนึงถึงการแก้ไขบัญชีเดิม
        account = Account.query.filter_by(name=name.data, organization_id=current_user.active_organization_id).first()

        # ถ้ามีบัญชีที่ใช้ชื่อนี้อยู่แล้ว และไม่ใช่บัญชีที่กำลังแก้ไข
        if account and (not self.id.data or int(self.id.data) != account.id):
            raise ValidationError('คุณมีบัญชีชื่อนี้อยู่แล้ว กรุณาใช้ชื่อบัญชีอื่น')