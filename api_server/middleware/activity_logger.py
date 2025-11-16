"""  
Flask middleware for automatic API activity logging  
Logs all POST/PUT/PATCH/DELETE requests  
"""  
  
from flask import request  
from core.activity_logger import ActivityLogger  
from app import db  
  
  
def log_api_activity(response):  
    """  
    After-request hook to log API operations  
    Called automatically by Flask after each request  
    """  
    # Only log mutation operations  
    if request.method in ['POST', 'PUT', 'PATCH', 'DELETE']:  
        try:  
            # Extract target entity from path  
            path = request.path  
            target_entity = None  
            target_id = None  
              
            if '/users/' in path:  
                target_entity = 'user'  
            elif '/products/' in path:  
                target_entity = 'product'  
            elif '/categories/' in path:  
                target_entity = 'category'  
            elif '/sales/' in path:  
                target_entity = 'sale'  
              
            # Extract ID from path if present  
            path_parts = path.split('/')  
            if len(path_parts) > 0 and path_parts[-1].isdigit():  
                target_id = int(path_parts[-1])  
              
            # Get IP address  
            ip_address = request.remote_addr  
              
            # Log the operation  
            ActivityLogger.log_api_operation(  
                method=request.method,  
                path=path,  
                target_entity=target_entity,  
                target_id=target_id,  
                ip_address=ip_address,  
                user_id=None  # No user ID in open API  
            )  
              
            db.session.commit()  
              
        except Exception as e:  
            print(f"Error logging API activity: {e}")  
            db.session.rollback()  
      
    return response  
  
  
def init_activity_logging(app):  
    """  
    Initialize activity logging middleware  
    Call this in app.py after creating the Flask app  
    """  
    app.after_request(log_api_activity)
