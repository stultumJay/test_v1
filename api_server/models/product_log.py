# api_server/models/product_log.py
from app import db
from datetime import datetime

class ProductLog(db.Model):
    __tablename__ = 'product_logs'
    id = db.Column(db.Integer, primary_key=True)
    product_id = db.Column(db.Integer, db.ForeignKey('products.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    action_type = db.Column(db.String(50), nullable=False)
    notes = db.Column(db.Text, nullable=True)
    log_time = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)

    def to_dict(self):
        return {
            'id': self.id,
            'product_id': self.product_id,
            'user_id': self.user_id,
            'action_type': self.action_type,
            'notes': self.notes,
            'log_time': self.log_time.isoformat()
        }
