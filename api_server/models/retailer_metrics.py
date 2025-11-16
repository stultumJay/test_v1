# api_server/models/retailer_metrics.py
from app import db
from datetime import date

class RetailerMetrics(db.Model):
    __tablename__ = 'retailer_metrics'
    id = db.Column(db.Integer, primary_key=True)
    retailer_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)

    current_streak = db.Column(db.Integer, default=0, nullable=False)
    daily_quota_usd = db.Column(db.Float, default=0.0, nullable=False)
    last_sale_date = db.Column(db.Date, nullable=True)

    def to_dict(self):
        return {
            'retailer_id': self.retailer_id,
            'current_streak': self.current_streak,
            'daily_quota_usd': self.daily_quota_usd,
            'last_sale_date': self.last_sale_date.isoformat() if self.last_sale_date else None
        }
