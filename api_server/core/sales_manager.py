# api_server/core/sales_manager.py
from app import db
from models.sale import Sale
from models.product import Product
from models.retailer_metrics import RetailerMetrics
from core.activity_logger import ActivityLogger
from datetime import date, timedelta
import json

class SalesManager:
    @staticmethod
    def record_atomic_sale(retailer_id, items, total_amount):
        """
        items: list of {product_id, quantity, price}
        Atomically:
          - validate stock
          - deduct stock
          - create Sale
          - update RetailerMetrics
        """
        try:
            if not items or total_amount is None:
                return None, "Invalid sale payload"

            # Validate & adjust stock
            for it in items:
                pid = it.get('product_id')
                qty = int(it.get('quantity', 0))
                if qty <= 0:
                    raise ValueError(f"Invalid quantity for product {pid}")
                product = Product.query.get(pid)
                if not product:
                    raise ValueError(f"Product {pid} not found")
                if product.stock_level < qty:
                    raise ValueError(f"Insufficient stock for product {pid}")
                product.stock_level -= qty

            # Create sale
            sale_json = json.dumps(items)
            sale = Sale(retailer_id=retailer_id, total_amount=total_amount, sale_items_json=sale_json)
            db.session.add(sale)

            # Update metrics
            metrics = RetailerMetrics.query.filter_by(retailer_id=retailer_id).first()
            if not metrics:
                metrics = RetailerMetrics(retailer_id=retailer_id)
                db.session.add(metrics)

            metrics.daily_quota_usd = (metrics.daily_quota_usd or 0.0) + float(total_amount)
            today = date.today()
            if metrics.last_sale_date is None:
                metrics.current_streak = 1
            else:
                # if last_sale_date is yesterday -> increment streak, else reset to 1
                try:
                    last = metrics.last_sale_date
                    if last == today:
                        pass  # multiple sales same day: don't alter streak
                    elif last == (today - timedelta(days=1)):
                        metrics.current_streak = (metrics.current_streak or 0) + 1
                    else:
                        metrics.current_streak = 1
                except Exception:
                    metrics.current_streak = 1
            metrics.last_sale_date = today

            # Log each product action (sale)
            for it in items:
                ActivityLogger.log_product_action(it.get('product_id'), retailer_id, 'Sale', f"Qty {it.get('quantity')}")

            db.session.commit()
            return sale, None
        except Exception as e:
            db.session.rollback()
            return None, str(e)

    @staticmethod
    def get_sales_report(start_date, end_date):
        # expects datetime or date objects
        q = Sale.query
        if start_date:
            q = q.filter(Sale.timestamp >= start_date)
        if end_date:
            q = q.filter(Sale.timestamp <= end_date)
        sales = q.all()
        total = sum(s.total_amount for s in sales)
        return {
            'total_revenue': total,
            'transactions': len(sales),
            'start_date': start_date.isoformat() if start_date else None,
            'end_date': end_date.isoformat() if end_date else None
        }
