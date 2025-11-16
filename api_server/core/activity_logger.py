# api_server/core/activity_logger.py
from app import db
from models.product_log import ProductLog
from datetime import datetime

class ActivityLogger:
    @staticmethod
    def log_product_action(product_id, user_id, action_type, notes=None):
        pl = ProductLog(product_id=product_id, user_id=user_id, action_type=action_type, notes=notes)
        db.session.add(pl)
        # Do not commit here to allow atomic commits in calling transactions
        return pl
