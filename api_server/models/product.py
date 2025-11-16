# api_server/models/product.py
from app import db
from datetime import date

class Product(db.Model):
    __tablename__ = 'products'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), unique=True, nullable=False)
    stock_level = db.Column(db.Integer, default=0, nullable=False)
    min_stock_level = db.Column(db.Integer, default=10, nullable=False)
    price = db.Column(db.Float, nullable=False)
    expiration_date = db.Column(db.Date, nullable=True)
    image_blob = db.Column(db.LargeBinary, nullable=True)

    category_id = db.Column(db.Integer, db.ForeignKey('categories.id'), nullable=True)

    log_entries = db.relationship('ProductLog', backref='product', lazy=True)

    def to_dict(self, include_image=False):
        d = {
            'id': self.id,
            'name': self.name,
            'stock_level': self.stock_level,
            'min_stock_level': self.min_stock_level,
            'price': float(self.price) if self.price is not None else None,
            'category_id': self.category_id,
            'expiration_date': self.expiration_date.isoformat() if self.expiration_date else None
        }
        if include_image and self.image_blob:
            import base64
            d['image_base64'] = base64.b64encode(self.image_blob).decode('utf-8')
        return d
