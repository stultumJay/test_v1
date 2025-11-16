# api_server/core/inventory_manager.py
from app import db
from models.product import Product
from core.activity_logger import ActivityLogger
from datetime import date, timedelta

class InventoryManager:
    @staticmethod
    def get_products(category_id=None, search=None):
        q = Product.query
        if category_id:
            q = q.filter(Product.category_id == category_id)
        if search:
            q = q.filter(Product.name.ilike(f"%{search}%"))
        return q.all()

    @staticmethod
    def update_stock(product_id, delta, acting_user_id=None, action_type='Restock', notes=None):
        product = Product.query.get(product_id)
        if not product:
            return False, "Product not found"
        product.stock_level = (product.stock_level or 0) + delta
        ActivityLogger.log_product_action(product_id, acting_user_id or 0, action_type, notes)
        db.session.commit()
        return True, None

    @staticmethod
    def get_low_stock():
        return Product.query.filter(Product.stock_level < Product.min_stock_level).all()

    @staticmethod
    def get_expiring(days=7):
        today = date.today()
        limit = today + timedelta(days=days)
        return Product.query.filter(Product.expiration_date.isnot(None), Product.expiration_date <= limit).all()
