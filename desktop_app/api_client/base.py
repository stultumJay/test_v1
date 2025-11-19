from typing import Any
from functools import wraps

class APIResponse:
    """Standardized API response wrapper"""
    def __init__(self, success: bool, data: Any = None, error: str = None, status_code: int = None):
        self.success = success
        self.data = data
        self.error = error
        self.status_code = status_code
    
    def __bool__(self):
        return self.success

def role_required(*allowed_roles):
    """
    Decorator to enforce RBAC on client methods.
    Imports current_session inside the wrapper to avoid circular imports with config.py.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Lazy import to prevent circular dependency with config.py
            from utils.config import current_session
            
            if not current_session.is_authenticated():
                return APIResponse(False, error="Not authenticated")
            
            user_role = current_session.role
            if user_role not in allowed_roles:
                return APIResponse(
                    False,
                    error=f"Access denied. Required roles: {', '.join(allowed_roles)}. Your role: {user_role}"
                )
            
            current_session.update_activity()
            return func(self, *args, **kwargs)
        return wrapper
    return decorator