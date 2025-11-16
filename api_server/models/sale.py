# api_server/models/sale.py
from app import db
from datetime import datetime

class Sale(db.Model):
    __tablename__ = 'sales'
    id = db.Column(db.Integer, primary_key=True)
    retailer_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    total_amount = db.Column(db.Float, nullable=False)
    # store items as JSON text
    sale_items_json = db.Column(db.Text, nullable=False)

    def to_dict(self):
        import json
        items = []
        try:
            items = json.loads(self.sale_items_json)
        except Exception:
            items = []
        return {
            'id': self.id,
            'retailer_id': self.retailer_id,
            'timestamp': self.timestamp.isoformat(),
            'total_amount': self.total_amount,
            'items': items
        }
