from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed
from wtforms import StringField, FloatField, TextAreaField, DateField, SelectField, SubmitField
from wtforms.validators import DataRequired, Optional, Length, NumberRange
from datetime import date

class TransactionForm(FlaskForm):
    amount = FloatField('จำนวนเงิน', validators=[DataRequired(), NumberRange(min=0.01)])
    description = TextAreaField('รายละเอียด', validators=[Optional(), Length(max=500)])
    transaction_date = DateField('วันที่', validators=[DataRequired()], default=date.today)
    type = SelectField('ประเภท', choices=[('income', 'รายรับ'), ('expense', 'รายจ่าย')], validators=[DataRequired()])
    category_id = SelectField('หมวดหมู่', coerce=int, validators=[DataRequired()])
    submit = SubmitField('บันทึก')

class CompanySettingsForm(FlaskForm):
    company_name = StringField('ชื่อบริษัท', validators=[Optional(), Length(max=200)])
    company_address = TextAreaField('ที่อยู่', validators=[Optional(), Length(max=500)])
    tax_id = StringField('เลขประจำตัวผู้เสียภาษี', validators=[Optional(), Length(max=20)])
    logo = FileField('โลโก้บริษัท', validators=[FileAllowed(['jpg', 'jpeg', 'png'], 'รองรับเฉพาะไฟล์รูปภาพ')])
    submit = SubmitField('บันทึก')

class CategoryForm(FlaskForm):
    name = StringField('ชื่อหมวดหมู่', validators=[DataRequired(), Length(max=100)])
    type = SelectField('ประเภท', choices=[('income', 'รายรับ'), ('expense', 'รายจ่าย')], validators=[DataRequired()])
    keywords = TextAreaField('คำสำคัญ (คั่นด้วยจุลภาค)', validators=[Optional(), Length(max=500)])
    submit = SubmitField('บันทึก')