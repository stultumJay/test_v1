"""  
Unified Activity Logger for StockaDoodle  
Handles both desktop app actions and direct API operations  
"""  
  
from app import db  
from models.product_log import ProductLog  
from datetime import datetime  
from typing import Optional, Dict  
import json  
  
  
class ActivityLogger:  
    """  
    Unified activity logging service  
    Logs to PRODUCT_LOG table with source detection (Desktop App vs API)  
    """  
      
    @staticmethod  
    def log_product_action(  
        product_id: int,  
        user_id: Optional[int],  
        action_type: str,  
        notes: Optional[str] = None,  
        source: str = "Desktop App"  
    ) -> ProductLog:  
        """  
        Log product-related actions (Restock, Sale, Dispose)  
          
        Args:  
            product_id: ID of the product  
            user_id: ID of the user performing action (None for API calls)  
            action_type: Type of action (Restock, Sale, Dispose)  
            notes: Additional notes about the action  
            source: Source of the action ("Desktop App" or "API")  
          
        Returns:  
            ProductLog instance (not committed)  
        """  
        log = ProductLog(  
            product_id=product_id,  
            user_id=user_id,  
            action_type=action_type,  
            notes=notes or f"Action performed via {source}",  
            log_time=datetime.utcnow()  
        )  
        db.session.add(log)  
        return log  
      
    @staticmethod  
    def log_user_action(  
        user_id: Optional[int],  
        action: str,  
        target: str,  
        details: Optional[Dict] = None,  
        source: str = "Desktop App",  
        ip_address: Optional[str] = None  
    ) -> ProductLog:  
        """  
        Log general user actions (login, user management, category management)  
        Uses PRODUCT_LOG table with product_id=NULL for non-product actions  
          
        Args:  
            user_id: ID of the user performing action (None for unauthenticated API calls)  
            action: Action type (e.g., "USER_ADDED", "CATEGORY_DELETED", "Logged In")  
            target: Target of the action (e.g., username, category name)  
            details: Additional details as dictionary  
            source: Source of the action ("Desktop App" or "API")  
            ip_address: IP address for API calls  
          
        Returns:  
            ProductLog instance (not committed)  
        """  
        notes_dict = {  
            "action": action,  
            "target": target,  
            "source": source,  
            "details": details or {}  
        }  
          
        if ip_address:  
            notes_dict["ip_address"] = ip_address  
          
        log = ProductLog(  
            product_id=None,  # NULL for non-product actions  
            user_id=user_id,  
            action_type=action,  
            notes=json.dumps(notes_dict),  
            log_time=datetime.utcnow()  
        )  
        db.session.add(log)  
        return log  
      
    @staticmethod  
    def log_api_operation(  
        method: str,  
        path: str,  
        target_entity: Optional[str] = None,  
        target_id: Optional[int] = None,  
        ip_address: Optional[str] = None,  
        user_id: Optional[int] = None  
    ) -> ProductLog:  
        """  
        Log direct API operations (Postman/ThunderClient calls)  
          
        Args:  
            method: HTTP method (POST, PUT, DELETE, PATCH)  
            path: API endpoint path  
            target_entity: Entity type (user, product, category, sale)  
            target_id: ID of the affected entity  
            ip_address: IP address of the caller  
            user_id: User ID if authenticated (None for open API)  
          
        Returns:  
            ProductLog instance (not committed)  
        """  
        notes_dict = {  
            "method": method,  
            "path": path,  
            "source": "API",  
            "ip_address": ip_address or "unknown"  
        }  
          
        if target_entity:  
            notes_dict["target_entity"] = target_entity  
        if target_id:  
            notes_dict["target_id"] = target_id  
          
        action_type = f"{method} {path}"  
          
        log = ProductLog(  
            product_id=None,  
            user_id=user_id,  
            action_type=action_type,  
            notes=json.dumps(notes_dict),  
            log_time=datetime.utcnow()  
        )  
        db.session.add(log)  
        return log  
      
    @staticmethod  
    def get_recent_logs(  
        limit: int = 50,  
        user_id: Optional[int] = None,  
        action_type: Optional[str] = None,  
        source: Optional[str] = None  
    ) -> list:  
        """  
        Query recent activity logs with optional filters  
          
        Args:  
            limit: Maximum number of logs to return  
            user_id: Filter by user ID  
            action_type: Filter by action type  
            source: Filter by source ("Desktop App" or "API")  
          
        Returns:  
            List of ProductLog instances  
        """  
        query = ProductLog.query  
          
        if user_id:  
            query = query.filter(ProductLog.user_id == user_id)  
          
        if action_type:  
            query = query.filter(ProductLog.action_type == action_type)  
          
        if source:  
            # Filter by source in notes JSON  
            query = query.filter(ProductLog.notes.like(f'%"source": "{source}"%'))  
          
        return query.order_by(ProductLog.log_time.desc()).limit(limit).all()
