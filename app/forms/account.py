# app/forms/account.py
from flask_wtf import FlaskForm
from wtforms import StringField, FloatField, BooleanField, HiddenField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, Optional, ValidationError
from app.models import Account

class AccountForm(FlaskForm):
    id = HiddenField('ID')
    name = StringField('ชื่อบัญชี', validators=[DataRequired(), Length(min=1, max=100)])
    account_number = StringField('เลขที่บัญชี', validators=[Optional(), Length(max=20)])
    bank_name = StringField('ธนาคาร', validators=[Optional(), Length(max=100)])
    balance = FloatField('ยอดเงินเริ่มต้น', default=0.0)
    is_active = BooleanField('เปิดใช้งาน', default=True)
    submit = SubmitField('บันทึก')

    def validate_name(self, field):
        # ตรวจสอบชื่อซ้ำภายในองค์กรเดียวกัน
        from flask_login import current_user
        account = Account.query.filter_by(
            name=field.data,
            organization_id=current_user.active_organization_id
        ).first()

        # ถ้ามีชื่อซ้ำ และไม่ใช่การแก้ไขตัวเอง
        if account and (not self.id.data or str(account.id) != str(self.id.data)):
            raise ValidationError('ชื่อบัญชีนี้มีอยู่ในระบบแล้ว โปรดใช้ชื่ออื่น')