# app/models/invitation.py
from datetime import datetime, timedelta
from app.extensions import db


class Invitation(db.Model):
    """โมเดลสำหรับจัดการลิงก์เชิญเข้าร่วมองค์กร"""
    __tablename__ = 'invitations'

    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(100), unique=True, nullable=False)
    organization_id = db.Column(db.Integer, db.ForeignKey('organizations.id'), nullable=False)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    role = db.Column(db.String(20), nullable=False, default='member')  # 'admin', 'member', 'viewer'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime, default=lambda: datetime.utcnow() + timedelta(days=7))
    used_at = db.Column(db.DateTime, nullable=True)
    used_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)

    # Relationships
    organization = db.relationship('Organization', backref='invitations')
    creator = db.relationship('User', foreign_keys=[created_by], backref='created_invitations')
    user = db.relationship('User', foreign_keys=[used_by], backref='used_invitations')

    def is_expired(self):
        """ตรวจสอบว่าลิงก์เชิญหมดอายุหรือยัง"""
        return datetime.utcnow() > self.expires_at

    def is_used(self):
        """ตรวจสอบว่าลิงก์เชิญถูกใช้แล้วหรือยัง"""
        return self.used_at is not None

    def mark_as_used(self, user_id):
        """ทำเครื่องหมายว่าลิงก์เชิญถูกใช้แล้ว"""
        self.used_at = datetime.utcnow()
        self.used_by = user_id
        db.session.commit()

    def __repr__(self):
        return f'<Invitation {self.token}>'