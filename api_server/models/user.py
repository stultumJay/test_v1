# api_server/models/user.py
from app import db
from sqlalchemy.sql import func
from datetime import datetime

class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    role = db.Column(db.String(20), default='Retailer')  # Admin, Manager, Retailer
    is_active = db.Column(db.Boolean, default=True)
    profile_pic_blob = db.Column(db.LargeBinary, nullable=True)
    created_at = db.Column(db.DateTime(timezone=True), server_default=func.now())

    # Relationships (defined as strings to avoid circular import issues on import time)
    # sales -> relationship from Sale model backref 'retailer'
    # metrics -> relationship from RetailerMetrics model backref 'retailer', uselist=False

    def to_dict(self, include_blob=False):
        d = {
            'id': self.id,
            'username': self.username,
            'role': self.role,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
        if include_blob and self.profile_pic_blob:
            import base64
            d['profile_pic_base64'] = base64.b64encode(self.profile_pic_blob).decode('utf-8')
        return d
