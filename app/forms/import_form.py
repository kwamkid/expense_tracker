# app/forms/import_form.py
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import SelectField, SubmitField, BooleanField
from wtforms.validators import DataRequired


class ImportForm(FlaskForm):
    """ฟอร์มสำหรับอัพโหลดไฟล์ธุรกรรมจากธนาคาร"""

    file = FileField('ไฟล์ Excel จากธนาคาร', validators=[
        FileRequired(),
        FileAllowed(['xlsx'], 'อนุญาตเฉพาะไฟล์ Excel (.xlsx) เท่านั้น')
    ])

    bank = SelectField('ธนาคาร', validators=[DataRequired()],
                       choices=[
                           ('scb', 'SCB - ธนาคารไทยพาณิชย์'),
                           # เพิ่มตัวเลือกธนาคารอื่นๆ ได้ในอนาคต
                           # ('kbank', 'KBANK - ธนาคารกสิกรไทย'),
                           # ('ktb', 'KTB - ธนาคารกรุงไทย'),
                       ])

    account_id = SelectField('บัญชีปลายทาง', coerce=int, validators=[DataRequired()])

    submit = SubmitField('อัพโหลดและวิเคราะห์ข้อมูล')


class ImportConfirmForm(FlaskForm):
    """ฟอร์มสำหรับยืนยันการนำเข้าธุรกรรม"""

    account_id = SelectField('บัญชีปลายทาง', coerce=int, validators=[DataRequired()])

    skip_duplicates = BooleanField('ข้ามรายการที่ซ้ำซ้อน', default=True)

    # จะมีฟิลด์สำหรับเลือกหมวดหมู่แต่ละรายการ แต่จะสร้างแบบไดนามิกในหน้าเทมเพลต

    submit = SubmitField('ยืนยันการนำเข้า')
    cancel = SubmitField('ยกเลิก', render_kw={'class': 'btn btn-secondary'})