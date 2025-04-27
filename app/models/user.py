# app/models/user.py
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from app.extensions import db


class User(UserMixin, db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    profile_image = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    active_organization_id = db.Column(db.Integer, nullable=True)  # องค์กรที่ผู้ใช้กำลังใช้งานอยู่
    # LINE Login fields
    line_id = db.Column(db.String(100), unique=True, nullable=True)
    line_profile_url = db.Column(db.String(255), nullable=True)

    # Relationships
    organizations = db.relationship('Organization', secondary='organization_users', back_populates='users')

    # Relationships กับตารางอื่นๆ ที่เกี่ยวข้องกับ User โดยตรง
    created_transactions = db.relationship('Transaction', foreign_keys='Transaction.created_by', backref='creator',
                                           lazy='dynamic')
    updated_transactions = db.relationship('Transaction', foreign_keys='Transaction.updated_by', backref='updater',
                                           lazy='dynamic')

    created_accounts = db.relationship('Account', foreign_keys='Account.created_by', backref='creator', lazy='dynamic')
    updated_accounts = db.relationship('Account', foreign_keys='Account.updated_by', backref='updater', lazy='dynamic')

    created_categories = db.relationship('Category', foreign_keys='Category.created_by', backref='creator',
                                         lazy='dynamic')
    updated_categories = db.relationship('Category', foreign_keys='Category.updated_by', backref='updater',
                                         lazy='dynamic')

    created_organizations = db.relationship('Organization', foreign_keys='Organization.created_by', backref='creator',
                                            lazy='dynamic')

    def __init__(self, username, email, password, first_name=None, last_name=None, line_id=None, line_profile_url=None):
        self.username = username
        self.email = email
        self.set_password(password)
        self.first_name = first_name
        self.last_name = last_name
        self.line_id = line_id
        self.line_profile_url = line_profile_url

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username

    def get_active_organization(self):
        """ดึงองค์กรที่ผู้ใช้กำลังใช้งานอยู่"""
        from app.models.organization import Organization
        if not self.active_organization_id:
            return None
        return Organization.query.get(self.active_organization_id)

    def set_active_organization(self, organization_id):
        """ตั้งค่าองค์กรที่ผู้ใช้กำลังใช้งาน"""
        self.active_organization_id = organization_id
        db.session.commit()

    def get_organizations(self):
        """ดึงองค์กรทั้งหมดที่ผู้ใช้เป็นสมาชิก"""
        return self.organizations

    def get_role_in_organization(self, organization_id):
        """ดึงบทบาทของผู้ใช้ในองค์กร"""
        from app.models.organization import organization_users
        result = db.session.execute(
            organization_users.select().where(
                (organization_users.c.user_id == self.id) &
                (organization_users.c.organization_id == organization_id)
            )
        ).first()

        return result.role if result else None

    def is_admin_of_active_org(self):
        """ตรวจสอบว่าผู้ใช้เป็นแอดมินในองค์กรที่กำลังใช้งานอยู่หรือไม่"""
        if not self.active_organization_id:
            return False
        role = self.get_role_in_organization(self.active_organization_id)
        return role == 'admin'

    def __repr__(self):
        return f'<User {self.username}>'