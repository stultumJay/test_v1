"""
StockaDoodle API Client
Provides RBAC enforcement and clean HTTP abstraction for PyQt desktop app
Uses global UserSession for unified state management
"""

import requests
import json
import base64
from functools import wraps
from typing import Dict, List, Optional, Any, Tuple


class APIResponse:
    """Standardized API response wrapper"""
    def __init__(self, success: bool, data: Any = None, error: str = None, status_code: int = None):
        self.success = success
        self.data = data
        self.error = error
        self.status_code = status_code
    
    def __bool__(self):
        return self.success
    
    def __repr__(self):
        if self.success:
            return f"<APIResponse success=True data={type(self.data).__name__}>"
        return f"<APIResponse success=False error='{self.error}'>"


def role_required(*allowed_roles):
    """
    Decorator to enforce RBAC on client methods
    Uses global current_session from utils.config
    Usage: @role_required('Admin', 'Manager')
    """
    from utils.config import current_session
    
    def decorator(func):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            if not current_session.is_authenticated():
                return APIResponse(False, error="Not authenticated")
            
            user_role = current_session.role
            if user_role not in allowed_roles:
                return APIResponse(
                    False,
                    error=f"Access denied. Required roles: {', '.join(allowed_roles)}. Your role: {user_role}"
                )
            
            # Update activity timestamp
            current_session.update_activity()
            
            return func(self, *args, **kwargs)
        return wrapper
    return decorator


class StockaDoodleAPI:
    """
    Main API client for StockaDoodle desktop application
    Handles all HTTP communication with the Flask backend
    Uses global UserSession for state management
    """
    
    def __init__(self, base_url: str = "http://127.0.0.1:5000/api/v1", timeout: int = 5):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        
        # Set custom User-Agent to identify as Desktop App
        self.headers = {
            'User-Agent': 'StockaDoodle-Desktop/1.0.0 (PyQt6)',
            'Content-Type': 'application/json'
        }
        
        # Initialize sub-clients
        self.users = UserClient(self)
        self.products = ProductClient(self)
        self.categories = CategoryClient(self)
        self.sales = SalesClient(self)
        self.logs = LogsClient(self)
        self.metrics = MetricsClient(self)
        self.dashboard = DashboardClient(self)
    
    def _url(self, path: str) -> str:
        """Build full URL from path"""
        return f"{self.base_url}/{path.lstrip('/')}"
    
    def _request(self, method: str, path: str, json_data: Dict = None, params: Dict = None) -> APIResponse:
        """
        Internal HTTP request handler with error handling
        Returns standardized APIResponse object
        """
        url = self._url(path)
        
        try:
            if method == 'GET':
                r = requests.get(url, params=params, headers=self.headers, timeout=self.timeout)
            elif method == 'POST':
                r = requests.post(url, json=json_data, headers=self.headers, timeout=self.timeout)
            elif method == 'PUT':
                r = requests.put(url, json=json_data, headers=self.headers, timeout=self.timeout)
            elif method == 'DELETE':
                r = requests.delete(url, headers=self.headers, timeout=self.timeout)
            else:
                return APIResponse(False, error=f"Unsupported HTTP method: {method}")
            
            # Try to parse JSON response
            try:
                data = r.json()
            except ValueError:
                data = r.text
            
            # Success codes
            if 200 <= r.status_code < 300:
                return APIResponse(True, data=data, status_code=r.status_code)
            
            # Error codes
            error_msg = data.get('error', str(data)) if isinstance(data, dict) else str(data)
            return APIResponse(False, error=error_msg, status_code=r.status_code)
            
        except requests.Timeout:
            return APIResponse(False, error="Request timeout - server not responding")
        except requests.ConnectionError:
            return APIResponse(False, error="Connection failed - is the server running?")
        except Exception as e:
            return APIResponse(False, error=f"Unexpected error: {str(e)}")
    
    def login(self, username: str, password: str) -> APIResponse:
        """
        Authenticate user and store session
        Returns: APIResponse with user data on success
        """
        resp = self._request('POST', 'users/auth/login', json_data={
            'username': username,
            'password': password
        })
        
        if resp.success:
            self.current_user = resp.data
        
        return resp
    
    def logout(self):
        """Clear current user session"""
        self.current_user = None
    
    def is_authenticated(self) -> bool:
        """Check if user is logged in"""
        return self.current_user is not None


class UserClient:
    """User management API client"""
    def __init__(self, api: StockaDoodleAPI):
        self.api = api
    
    @role_required('Admin')
    def list(self) -> APIResponse:
        """GET /users - List all users"""
        return self.api._request('GET', 'users')
    
    @role_required('Admin')
    def create(self, username: str, password: str, role: str = 'Retailer', email: str = None) -> APIResponse:
        """POST /users - Create new user"""
        return self.api._request('POST', 'users', json_data={
            'username': username,
            'password': password,
            'role': role,
            'email': email
        })
    
    @role_required('Admin')
    def get(self, user_id: int) -> APIResponse:
        """GET /users/<id>"""
        return self.api._request('GET', f'users/{user_id}')
    
    @role_required('Admin')
    def update(self, user_id: int, **kwargs) -> APIResponse:
        """PUT /users/<id>"""
        return self.api._request('PUT', f'users/{user_id}', json_data=kwargs)
    
    @role_required('Admin')
    def delete(self, user_id: int) -> APIResponse:
        """DELETE /users/<id>"""
        return self.api._request('DELETE', f'users/{user_id}')


class ProductClient:
    """Product management API client"""
    def __init__(self, api: StockaDoodleAPI):
        self.api = api
    
    def list(self, category_id: int = None, search: str = None, include_image: bool = False) -> APIResponse:
        """GET /products - List products with optional filters"""
        params = {}
        if category_id:
            params['category_id'] = category_id
        if search:
            params['search'] = search
        if include_image:
            params['include_image'] = 'true'
        
        return self.api._request('GET', 'products', params=params)
    
    def get(self, product_id: int, include_image: bool = False) -> APIResponse:
        """GET /products/<id>"""
        params = {'include_image': 'true'} if include_image else {}
        return self.api._request('GET', f'products/{product_id}', params=params)
    
    @role_required('Admin', 'Manager')
    def create(self, name: str, price: float, **kwargs) -> APIResponse:
        """POST /products - Create new product"""
        data = {'name': name, 'price': price, **kwargs}
        
        # Handle image file path -> Base64
        if 'image_path' in kwargs and kwargs['image_path']:
            try:
                with open(kwargs['image_path'], 'rb') as f:
                    image_data = f.read()
                    data['image_base64'] = base64.b64encode(image_data).decode('utf-8')
                del data['image_path']
            except Exception as e:
                return APIResponse(False, error=f"Failed to read image: {e}")
        
        return self.api._request('POST', 'products', json_data=data)
    
    @role_required('Admin', 'Manager')
    def update(self, product_id: int, **kwargs) -> APIResponse:
        """PUT /products/<id>"""
        data = dict(kwargs)
        
        # Handle image file path -> Base64
        if 'image_path' in kwargs and kwargs['image_path']:
            try:
                with open(kwargs['image_path'], 'rb') as f:
                    image_data = f.read()
                    data['image_base64'] = base64.b64encode(image_data).decode('utf-8')
                del data['image_path']
            except Exception as e:
                return APIResponse(False, error=f"Failed to read image: {e}")
        
        return self.api._request('PUT', f'products/{product_id}', json_data=data)
    
    @role_required('Admin', 'Manager')
    def delete(self, product_id: int) -> APIResponse:
        """DELETE /products/<id>"""
        return self.api._request('DELETE', f'products/{product_id}')


class CategoryClient:
    """Category management API client"""
    def __init__(self, api: StockaDoodleAPI):
        self.api = api
    
    def list(self) -> APIResponse:
        """GET /categories"""
        return self.api._request('GET', 'categories')
    
    @role_required('Admin', 'Manager')
    def create(self, name: str) -> APIResponse:
        """POST /categories"""
        return self.api._request('POST', 'categories', json_data={'name': name})
    
    @role_required('Admin', 'Manager')
    def update(self, category_id: int, name: str) -> APIResponse:
        """PUT /categories/<id>"""
        return self.api._request('PUT', f'categories/{category_id}', json_data={'name': name})
    
    @role_required('Admin', 'Manager')
    def delete(self, category_id: int) -> APIResponse:
        """DELETE /categories/<id>"""
        return self.api._request('DELETE', f'categories/{category_id}')


class SalesClient:
    """Sales transaction API client"""
    def __init__(self, api: StockaDoodleAPI):
        self.api = api
    
    @role_required('Admin', 'Manager', 'Retailer')
    def record(self, retailer_id: int, items: List[Dict], total_amount: float) -> APIResponse:
        """
        POST /sales - Record atomic sale transaction
        items: [{'product_id': int, 'quantity': int, 'price': float}, ...]
        """
        return self.api._request('POST', 'sales', json_data={
            'retailer_id': retailer_id,
            'items': items,
            'total_amount': total_amount
        })
    
    @role_required('Admin', 'Manager')
    def undo(self, sale_id: int) -> APIResponse:
        """DELETE /sales/<id> - Undo sale (restore stock)"""
        return self.api._request('DELETE', f'sales/{sale_id}')
    
    @role_required('Admin', 'Manager')
    def reports(self, start_date: str = None, end_date: str = None) -> APIResponse:
        """GET /sales/reports?start=&end="""
        params = {}
        if start_date:
            params['start'] = start_date
        if end_date:
            params['end'] = end_date
        return self.api._request('GET', 'sales/reports', params=params)


class LogsClient:
    """Activity logs API client"""
    def __init__(self, api: StockaDoodleAPI):
        self.api = api
    
    def for_product(self, product_id: int) -> APIResponse:
        """GET /log/product/<id>"""
        return self.api._request('GET', f'log/product/{product_id}')
    
    def for_user(self, user_id: int) -> APIResponse:
        """GET /log/user/<id>"""
        return self.api._request('GET', f'log/user/{user_id}')
    
    @role_required('Admin', 'Manager')
    def dispose(self, product_id: int, user_id: int, quantity: int, notes: str = None) -> APIResponse:
        """POST /log/dispose - Atomic product disposal"""
        return self.api._request('POST', 'log/dispose', json_data={
            'product_id': product_id,
            'user_id': user_id,
            'quantity': quantity,
            'notes': notes
        })
    
    def log_desktop_action(self, action_data: Dict) -> APIResponse:
        """
        Log desktop application activity
        Sends to backend for centralized audit trail
        
        Args:
            action_data: Dict with action details (user_id, action_type, target, etc.)
        """
        return self.api._request('POST', 'log/desktop', json_data=action_data)


class MetricsClient:
    """Retailer metrics API client"""
    def __init__(self, api: StockaDoodleAPI):
        self.api = api
    
    def get(self, user_id: int) -> APIResponse:
        """GET /retailer/<id> - Get retailer metrics"""
        return self.api._request('GET', f'retailer/{user_id}')
    
    def leaderboard(self) -> APIResponse:
        """GET /retailer/leaderboard"""
        return self.api._request('GET', 'retailer/leaderboard')


class DashboardClient:
    """Dashboard summary data API client"""
    def __init__(self, api: StockaDoodleAPI):
        self.api = api
    
    @role_required('Admin')
    def admin(self) -> APIResponse:
        """GET /dashboard/admin"""
        return self.api._request('GET', 'dashboard/admin')
    
    @role_required('Admin', 'Manager')
    def manager(self) -> APIResponse:
        """GET /dashboard/manager"""
        return self.api._request('GET', 'dashboard/manager')
    
    def retailer(self, user_id: int) -> APIResponse:
        """GET /dashboard/retailer/<id>"""
        return self.api._request('GET', f'dashboard/retailer/{user_id}')


# Example usage
if __name__ == '__main__':
    # Initialize API client
    api = StockaDoodleAPI()
    
    # Login as admin
    resp = api.login('admin', 'admin')
    if resp.success:
        print(f"Logged in as: {resp.data['username']} ({resp.data['role']})")
        
        # Try admin operation
        users_resp = api.users.list()
        if users_resp.success:
            print(f"Found {len(users_resp.data)} users")
        
        # Try creating product (allowed for Admin)
        prod_resp = api.products.create(
            name="Test Product",
            price=99.99,
            stock_level=10
        )
        print(f"Create product: {prod_resp.success}")
    
    # Login as retailer
    api.logout()
    resp = api.login('retailer', 'password')
    if resp.success:
        print(f"\nLogged in as: {resp.data['username']} ({resp.data['role']})")
        
        # Try admin operation (should fail)
        users_resp = api.users.list()
        print(f"Retailer trying to list users: {users_resp.success}")
        if not users_resp.success:
            print(f"Error: {users_resp.error}")

