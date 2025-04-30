# app/forms/category.py
from flask_wtf import FlaskForm
from wtforms import StringField, SelectField, SubmitField, HiddenField
from wtforms.validators import DataRequired, Length, ValidationError
from app.models import Category
from flask_login import current_user


class CategoryForm(FlaskForm):
    id = HiddenField('ID')  # เพิ่มฟิลด์นี้

    name = StringField('ชื่อหมวดหมู่', validators=[DataRequired(), Length(max=100)])
    type = SelectField('ประเภท', choices=[('income', 'รายรับ'), ('expense', 'รายจ่าย')], validators=[DataRequired()])
    color = StringField('สี (รหัส HEX)', default='#3498db')
    icon = StringField('ไอคอน', description='ชื่อไอคอนจาก Font Awesome เช่น "money-bill", "car"')
    submit = SubmitField('บันทึก')

    def validate_name(self, name):
        # สร้างตัวแปรเก็บ ID ของหมวดหมู่ที่กำลังแก้ไข (ถ้ามี)
        current_id = None
        if hasattr(self, 'id') and self.id.data:
            current_id = int(self.id.data)
        elif hasattr(self, '_obj') and self._obj and hasattr(self._obj, 'id'):
            current_id = self._obj.id

        # ค้นหาหมวดหมู่ที่มีชื่อเดียวกัน ประเภทเดียวกัน ในองค์กรเดียวกัน
        category = Category.query.filter_by(
            name=name.data,
            type=self.type.data,
            organization_id=current_user.active_organization_id
        ).first()

        # ถ้าพบหมวดหมู่และไม่ใช่รายการที่กำลังแก้ไข
        if category and (current_id is None or category.id != current_id):
            raise ValidationError(f'คุณมีหมวดหมู่ "{name.data}" ในประเภท {self.type.data} อยู่แล้ว')