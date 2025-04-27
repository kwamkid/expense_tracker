# app/forms/auth.py
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError, Optional
from app.models import User


class LoginForm(FlaskForm):
    email = StringField('อีเมล', validators=[DataRequired(), Email()])
    password = PasswordField('รหัสผ่าน', validators=[DataRequired()])
    remember = BooleanField('จดจำฉัน')
    submit = SubmitField('เข้าสู่ระบบ')


class RegistrationForm(FlaskForm):
    username = StringField('ชื่อผู้ใช้', validators=[DataRequired(), Length(min=4, max=25)])
    email = StringField('อีเมล', validators=[DataRequired(), Email()])
    first_name = StringField('ชื่อจริง', validators=[Optional(), Length(max=100)])
    last_name = StringField('นามสกุล', validators=[Optional(), Length(max=100)])
    password = PasswordField('รหัสผ่าน', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('ยืนยันรหัสผ่าน', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('สมัครสมาชิก')

    def validate_username(self, username):
        user = User.query.filter_by(username=username.data).first()
        if user:
            raise ValidationError('ชื่อผู้ใช้นี้ถูกใช้ไปแล้ว กรุณาเลือกชื่ออื่น')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('อีเมลนี้ถูกลงทะเบียนไปแล้ว กรุณาใช้อีเมลอื่น')


class PasswordResetRequestForm(FlaskForm):
    email = StringField('อีเมล', validators=[DataRequired(), Email()])
    submit = SubmitField('ส่งลิงก์รีเซ็ตรหัสผ่าน')

    def validate_email(self, email):
        user = User.query.filter_by(email=email.data).first()
        if user is None:
            raise ValidationError('ไม่พบบัญชีที่ใช้อีเมลนี้ กรุณาตรวจสอบอีเมลอีกครั้ง')


class PasswordResetForm(FlaskForm):
    password = PasswordField('รหัสผ่านใหม่', validators=[DataRequired(), Length(min=6)])
    confirm_password = PasswordField('ยืนยันรหัสผ่านใหม่', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('บันทึกรหัสผ่านใหม่')