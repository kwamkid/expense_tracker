# app/models/organization.py
from datetime import datetime
from app.extensions import db

# ตารางความสัมพันธ์ระหว่าง User และ Organization
organization_users = db.Table('organization_users',
                              db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
                              db.Column('organization_id', db.Integer, db.ForeignKey('organizations.id'),
                                        primary_key=True),
                              db.Column('role', db.String(20), nullable=False, default='member'),
                              # 'admin', 'member', 'viewer'
                              db.Column('joined_at', db.DateTime, default=datetime.utcnow)
                              )


class Organization(db.Model):
    __tablename__ = 'organizations'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text, nullable=True)
    logo_path = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'))
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    accounts = db.relationship('Account', backref='organization', lazy='dynamic', cascade='all, delete-orphan')
    categories = db.relationship('Category', backref='organization', lazy='dynamic', cascade='all, delete-orphan')
    transactions = db.relationship('Transaction', backref='organization', lazy='dynamic', cascade='all, delete-orphan')
    users = db.relationship('User', secondary=organization_users, back_populates='organizations')

    def __repr__(self):
        return f'<Organization {self.name}>'

    # ฟังก์ชั่นตรวจสอบว่าผู้ใช้มีบทบาทอะไรในองค์กร
    def get_user_role(self, user_id):
        result = db.session.execute(
            organization_users.select().where(
                (organization_users.c.user_id == user_id) &
                (organization_users.c.organization_id == self.id)
            )
        ).first()

        return result.role if result else None

    # ฟังก์ชั่นตรวจสอบว่าผู้ใช้มีสิทธิ์นั้นหรือไม่
    def user_has_role(self, user_id, roles):
        if isinstance(roles, str):
            roles = [roles]

        user_role = self.get_user_role(user_id)
        return user_role in roles