# desktop_app/utils/decorators.py
"""
Decorators for role-based access control and logging
Client-side enforcement without UI popups
"""
from functools import wraps
import logging
from typing import Callable, Any
from utils.config import current_session

# Setup logging
logger = logging.getLogger('stockadoodle.rbac')


class PermissionDeniedError(Exception):
    """Raised when user lacks required permissions"""
    def __init__(self, required_roles, user_role):
        self.required_roles = required_roles
        self.user_role = user_role
        super().__init__(
            f"Permission denied. Required roles: {', '.join(required_roles)}. "
            f"User role: {user_role or 'Not authenticated'}"
        )


class SessionExpiredError(Exception):
    """Raised when user session has expired"""
    pass


def role_required(*allowed_roles: str):
    """
    Decorator to enforce role-based access control
    Raises PermissionDeniedError if user lacks required role
    
    Usage:
        @role_required('Admin', 'Manager')
        def delete_user(user_id):
            ...
    
    Args:
        allowed_roles: Variable number of role names that are allowed
    
    Raises:
        PermissionDeniedError: If user role not in allowed_roles
        SessionExpiredError: If session has expired
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Check if authenticated
            if not current_session.is_authenticated():
                logger.warning(f"Unauthenticated access attempt to {func.__name__}")
                raise PermissionDeniedError(allowed_roles, None)
            
            # Check session expiry
            if current_session.is_session_expired():
                logger.warning(f"Expired session access attempt to {func.__name__}")
                raise SessionExpiredError("Session has expired. Please login again.")
            
            # Check role
            if not current_session.has_role(*allowed_roles):
                logger.warning(
                    f"Access denied for {current_session.username} ({current_session.role}) "
                    f"to {func.__name__}. Required: {allowed_roles}"
                )
                raise PermissionDeniedError(allowed_roles, current_session.role)
            
            # Update activity timestamp
            current_session.update_activity()
            
            # Log successful access
            logger.info(
                f"{current_session.username} ({current_session.role}) "
                f"accessed {func.__name__}"
            )
            
            # Execute function
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


def authenticated_only(func: Callable) -> Callable:
    """
    Decorator to ensure user is authenticated
    Lighter check than role_required - just needs any valid session
    
    Usage:
        @authenticated_only
        def view_profile():
            ...
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not current_session.is_authenticated():
            logger.warning(f"Unauthenticated access attempt to {func.__name__}")
            raise PermissionDeniedError(['Any authenticated user'], None)
        
        if current_session.is_session_expired():
            logger.warning(f"Expired session access attempt to {func.__name__}")
            raise SessionExpiredError("Session has expired. Please login again.")
        
        current_session.update_activity()
        return func(*args, **kwargs)
    
    return wrapper


def log_action(action_type: str, target_entity: str = None):
    """
    Decorator to log user actions
    Sends activity log to backend via API
    
    Usage:
        @log_action('CREATE', 'product')
        def create_product(data):
            ...
    
    Args:
        action_type: Type of action (CREATE, UPDATE, DELETE, VIEW)
        target_entity: Entity being acted upon (product, user, category)
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Execute function first
            result = func(*args, **kwargs)
            
            # Log action after successful execution
            try:
                if current_session.is_authenticated():
                    log_data = {
                        'user_id': current_session.user_id,
                        'username': current_session.username,
                        'action_type': action_type,
                        'target_entity': target_entity,
                        'function_name': func.__name__,
                        'args': str(args)[:100],  # Truncate for security
                        'kwargs': str(kwargs)[:100]
                    }
                    logger.info(f"Action logged: {log_data}")
                    
                    # TODO: Send to backend API when implemented
                    # api.logs.log_desktop_action(log_data)
            except Exception as e:
                # Don't break function if logging fails
                logger.error(f"Failed to log action: {e}")
            
            return result
        
        return wrapper
    return decorator


def retry_on_failure(max_attempts: int = 3, delay: float = 1.0):
    """
    Decorator to retry function on failure
    Useful for API calls that may timeout
    
    Usage:
        @retry_on_failure(max_attempts=3, delay=2.0)
        def fetch_products():
            ...
    
    Args:
        max_attempts: Maximum number of retry attempts
        delay: Delay in seconds between retries
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            import time
            
            last_exception = None
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_attempts - 1:
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_attempts} failed for {func.__name__}: {e}. "
                            f"Retrying in {delay}s..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"All {max_attempts} attempts failed for {func.__name__}: {e}"
                        )
            
            # Re-raise the last exception after all attempts
            raise last_exception
        
        return wrapper
    return decorator


def cache_result(timeout_seconds: int = 300):
    """
    Decorator to cache function results for a specified time
    Useful for frequently accessed data that doesn't change often
    
    Usage:
        @cache_result(timeout_seconds=60)
        def get_categories():
            ...
    
    Args:
        timeout_seconds: Cache validity duration in seconds
    """
    def decorator(func: Callable) -> Callable:
        cache = {}
        cache_time = {}
        
        @wraps(func)
        def wrapper(*args, **kwargs):
            import time
            
            # Create cache key from function name and arguments
            cache_key = f"{func.__name__}:{str(args)}:{str(kwargs)}"
            
            # Check if cached result exists and is still valid
            if cache_key in cache:
                if time.time() - cache_time[cache_key] < timeout_seconds:
                    logger.debug(f"Cache hit for {func.__name__}")
                    return cache[cache_key]
            
            # Execute function and cache result
            logger.debug(f"Cache miss for {func.__name__}")
            result = func(*args, **kwargs)
            cache[cache_key] = result
            cache_time[cache_key] = time.time()
            
            return result
        
        # Add method to clear cache
        wrapper.clear_cache = lambda: cache.clear()
        
        return wrapper
    return decorator


def validate_input(**validators):
    """
    Decorator to validate function input arguments
    
    Usage:
        @validate_input(
            username=lambda x: len(x) >= 3,
            age=lambda x: x >= 0
        )
        def create_user(username, age):
            ...
    
    Args:
        validators: Dict of argument_name -> validation_function
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get function signature to map args to names
            import inspect
            sig = inspect.signature(func)
            bound_args = sig.bind(*args, **kwargs)
            bound_args.apply_defaults()
            
            # Validate each argument
            for param_name, validator_func in validators.items():
                if param_name in bound_args.arguments:
                    value = bound_args.arguments[param_name]
                    if not validator_func(value):
                        raise ValueError(
                            f"Validation failed for parameter '{param_name}': {value}"
                        )
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


# Example usage and testing
if __name__ == '__main__':
    # Setup logging
    logging.basicConfig(level=logging.INFO)
    
    # Test role_required
    @role_required('Admin', 'Manager')
    def delete_user(user_id):
        return f"User {user_id} deleted"
    
    # Test without login (should fail)
    try:
        delete_user(123)
        print("ERROR: Should have raised PermissionDeniedError")
    except PermissionDeniedError as e:
        print(f"✓ Correctly denied: {e}")
    
    # Test with login
    current_session.login({
        'id': 1,
        'username': 'admin',
        'role': 'Admin',
        'email': 'admin@test.com'
    })
    
    try:
        result = delete_user(123)
        print(f"✓ Access granted: {result}")
    except Exception as e:
        print(f"ERROR: {e}")
    
    # Test retry
    @retry_on_failure(max_attempts=3, delay=0.1)
    def flaky_function():
        import random
        if random.random() < 0.7:
            raise Exception("Random failure")
        return "Success"
    
    try:
        print(f"✓ Retry result: {flaky_function()}")
    except Exception as e:
        print(f"✗ Failed after retries: {e}")