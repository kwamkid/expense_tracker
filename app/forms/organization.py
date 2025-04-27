# app/forms/organization.py
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, TextAreaField, SubmitField, SelectField
from wtforms.validators import DataRequired, Length, Email, ValidationError, Optional
from app.models.organization import Organization
from app.models.user import User
from flask_login import current_user


class OrganizationForm(FlaskForm):
    """ฟอร์มสำหรับสร้างหรือแก้ไของค์กร"""
    name = StringField('ชื่อองค์กร', validators=[DataRequired(), Length(min=2, max=100)])
    description = TextAreaField('รายละเอียด', validators=[Optional(), Length(max=500)])
    logo = FileField('โลโก้', validators=[
        Optional(),
        FileAllowed(['jpg', 'jpeg', 'png', 'gif'], 'อนุญาตเฉพาะไฟล์รูปภาพเท่านั้น')
    ])
    submit = SubmitField('บันทึก')

    def validate_name(self, name):
        # ตรวจสอบชื่อซ้ำโดยคำนึงถึงการแก้ไของค์กรเดิม
        if hasattr(self, 'id') and self.id.data:
            # กรณีแก้ไของค์กรเดิม
            organization = Organization.query.filter_by(name=name.data).first()
            if organization and organization.id != int(self.id.data):
                raise ValidationError('ชื่อองค์กรนี้ถูกใช้ไปแล้ว กรุณาใช้ชื่ออื่น')
        else:
            # กรณีสร้างองค์กรใหม่
            if Organization.query.filter_by(name=name.data).first():
                raise ValidationError('ชื่อองค์กรนี้ถูกใช้ไปแล้ว กรุณาใช้ชื่ออื่น')


class InviteForm(FlaskForm):
    """ฟอร์มสำหรับเชิญสมาชิกเข้าร่วมองค์กร"""
    email = StringField('อีเมล', validators=[DataRequired(), Email()])
    role = SelectField('บทบาท', choices=[
        ('admin', 'แอดมิน - จัดการได้ทุกอย่าง'),
        ('member', 'สมาชิก - เพิ่ม/แก้ไขรายการได้'),
        ('viewer', 'ผู้ชม - ดูข้อมูลได้อย่างเดียว')
    ], default='member', validators=[DataRequired()])
    submit = SubmitField('เชิญ')

    def validate_email(self, email):
        # ตรวจสอบว่าอีเมลนี้มีในระบบหรือไม่
        user = User.query.filter_by(email=email.data).first()
        if not user:
            raise ValidationError('ไม่พบอีเมลนี้ในระบบ ผู้ใช้ต้องลงทะเบียนในระบบก่อน')

        # ตรวจสอบว่าไม่ใช่อีเมลของผู้เชิญเอง
        if user.id == current_user.id:
            raise ValidationError('คุณไม่สามารถเชิญตัวเองได้')