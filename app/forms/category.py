# app/forms/category.py
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length, ValidationError
from app.models import Category
from flask_login import current_user


class CategoryForm(FlaskForm):
    name = StringField('ชื่อหมวดหมู่', validators=[DataRequired(), Length(max=100)])
    type = SelectField('ประเภท', choices=[('income', 'รายรับ'), ('expense', 'รายจ่าย')], validators=[DataRequired()])
    color = StringField('สี (รหัส HEX)', default='#3498db')
    icon = StringField('ไอคอน', description='ชื่อไอคอนจาก Font Awesome เช่น "money-bill", "car"')
    submit = SubmitField('บันทึก')

    def validate_name(self, name):
        # ตรวจสอบเฉพาะในโหมดสร้างใหม่ (ไม่มี id)
        if not hasattr(self, 'id') or not self.id.data:
            category = Category.query.filter_by(
                name=name.data,
                type=self.type.data,
                organization_id=current_user.active_organization_id
            ).first()
            if category:
                raise ValidationError(f'คุณมีหมวดหมู่ "{name.data}" ในประเภท {self.type.data} อยู่แล้ว')