# desktop_app/utils/config.py
"""
Configuration constants and session management for StockaDoodle Desktop App
"""
import os
from typing import Optional, Dict
from datetime import datetime


class AppConfig:
    """Application-wide configuration constants"""
    
    # API Configuration
    BASE_URL = os.getenv('STOCKADOODLE_API_URL', 'http://127.0.0.1:5000/api/v1')
    API_TIMEOUT = int(os.getenv('API_TIMEOUT', '10'))  # seconds
    
    # Application Info
    APP_NAME = "StockaDoodle IMS"
    APP_VERSION = "1.0.0"
    USER_AGENT = f"StockaDoodle-Desktop/{APP_VERSION} (PyQt6)"
    
    # MFA Configuration  
    MFA_SENDER_EMAIL = os.getenv('MFA_SENDER_EMAIL', 'noreply@stockadoodle.com')  
    MFA_CODE_LENGTH = int(os.getenv('MFA_CODE_LENGTH', '6'))  
    MFA_CODE_EXPIRY_MINUTES = int(os.getenv('MFA_CODE_EXPIRY_MINUTES', '5'))  
      
    # SMTP Configuration  
    SMTP_SERVER = os.getenv('SMTP_SERVER', 'smtp.gmail.com')  
    SMTP_PORT = int(os.getenv('SMTP_PORT', '587'))  
    SMTP_USERNAME = os.getenv('SMTP_USERNAME', 'your_email@gmail.com')  
    SMTP_PASSWORD = os.getenv('SMTP_PASSWORD', 'your_app_password')
    
    # Theme Colors (Material Design inspired)
    PRIMARY_COLOR = "#6C5CE7"      # Vibrant purple
    SECONDARY_COLOR = "#00B894"    # Teal/green
    ACCENT_COLOR = "#D63031"       # Red for errors
    BACKGROUND_COLOR = "#2C3E50"   # Dark blue-gray
    CARD_BACKGROUND = "#34495E"    # Lighter card background
    TEXT_COLOR = "#ECF0F1"         # Light text
    TEXT_SECONDARY = "#BDC3C7"     # Secondary text
    
    # Status Colors
    SUCCESS_COLOR = "#00B894"      # Green
    WARNING_COLOR = "#FDCB6E"      # Yellow/orange
    ERROR_COLOR = "#D63031"        # Red
    INFO_COLOR = "#74B9FF"         # Light blue
    
    # Font Configuration
    FONT_FAMILY = "Segoe UI, Inter, sans-serif"
    FONT_SIZE_SMALL = 9
    FONT_SIZE_NORMAL = 10
    FONT_SIZE_MEDIUM = 12
    FONT_SIZE_LARGE = 14
    FONT_SIZE_XLARGE = 18
    
    # UI Layout
    SIDEBAR_WIDTH = 220
    WINDOW_MIN_WIDTH = 1024
    WINDOW_MIN_HEIGHT = 768
    
    # Business Rules
    DEFAULT_MIN_STOCK_LEVEL = 10
    LOW_STOCK_WARNING_DAYS = 7
    SESSION_TIMEOUT_MINUTES = 60
    
    # File Paths
    LOG_DIR = os.path.join(os.getcwd(), 'logs')
    CACHE_DIR = os.path.join(os.getcwd(), '.cache')
    
    @classmethod
    def ensure_directories(cls):
        """Create necessary directories if they don't exist"""
        os.makedirs(cls.LOG_DIR, exist_ok=True)
        os.makedirs(cls.CACHE_DIR, exist_ok=True)


class UserSession:
    """
    Manages current user session state
    Singleton pattern - only one active session
    """
    _instance: Optional['UserSession'] = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(UserSession, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._user_id: Optional[int] = None
        self._username: Optional[str] = None
        self._role: Optional[str] = None
        self._email: Optional[str] = None
        self._login_time: Optional[datetime] = None
        self._last_activity: Optional[datetime] = None
        self._session_data: Dict = {}
        self._initialized = True
    
    def login(self, user_data: Dict):
        """
        Initialize session with user data from API login
        Args:
            user_data: Dict with keys: id, username, role, email
        """
        self._user_id = user_data.get('id')
        self._username = user_data.get('username')
        self._role = user_data.get('role')
        self._email = user_data.get('email')
        self._login_time = datetime.now()
        self._last_activity = datetime.now()
        self._session_data = {}
    
    def logout(self):
        """Clear all session data"""
        self._user_id = None
        self._username = None
        self._role = None
        self._email = None
        self._login_time = None
        self._last_activity = None
        self._session_data = {}
    
    def is_authenticated(self) -> bool:
        """Check if user is logged in"""
        return self._user_id is not None
    
    def update_activity(self):
        """Update last activity timestamp"""
        self._last_activity = datetime.now()
    
    def is_session_expired(self) -> bool:
        """Check if session has expired based on inactivity"""
        if not self._last_activity:
            return True
        
        from datetime import timedelta
        timeout = timedelta(minutes=AppConfig.SESSION_TIMEOUT_MINUTES)
        return (datetime.now() - self._last_activity) > timeout
    
    @property
    def user_id(self) -> Optional[int]:
        return self._user_id
    
    @property
    def username(self) -> Optional[str]:
        return self._username
    
    @property
    def role(self) -> Optional[str]:
        return self._role
    
    @property
    def email(self) -> Optional[str]:
        return self._email
    
    @property
    def login_time(self) -> Optional[datetime]:
        return self._login_time
    
    def has_role(self, *roles) -> bool:
        """
        Check if current user has any of the specified roles
        Args:
            roles: Variable number of role names to check
        Returns:
            True if user has any of the roles
        """
        if not self.is_authenticated():
            return False
        return self._role in roles
    
    def is_admin(self) -> bool:
        """Check if current user is admin"""
        return self.has_role('Admin')
    
    def is_manager(self) -> bool:
        """Check if current user is manager"""
        return self.has_role('Manager')
    
    def is_retailer(self) -> bool:
        """Check if current user is retailer"""
        return self.has_role('Retailer')
    
    def can_manage_users(self) -> bool:
        """Check if user can manage other users"""
        return self.is_admin()
    
    def can_manage_products(self) -> bool:
        """Check if user can add/edit/delete products"""
        return self.has_role('Admin', 'Manager')
    
    def can_manage_categories(self) -> bool:
        """Check if user can add/edit/delete categories"""
        return self.has_role('Admin', 'Manager')
    
    def can_undo_sales(self) -> bool:
        """Check if user can undo sales transactions"""
        return self.has_role('Admin', 'Manager')
    
    def can_dispose_products(self) -> bool:
        """Check if user can dispose of products"""
        return self.has_role('Admin', 'Manager')
    
    def can_view_admin_dashboard(self) -> bool:
        """Check if user can view admin dashboard"""
        return self.is_admin()
    
    def can_view_manager_dashboard(self) -> bool:
        """Check if user can view manager dashboard"""
        return self.has_role('Admin', 'Manager')
    
    def set_session_data(self, key: str, value):
        """Store arbitrary session data"""
        self._session_data[key] = value
    
    def get_session_data(self, key: str, default=None):
        """Retrieve session data"""
        return self._session_data.get(key, default)
    
    def to_dict(self) -> Dict:
        """Export session data as dictionary"""
        return {
            'user_id': self._user_id,
            'username': self._username,
            'role': self._role,
            'email': self._email,
            'login_time': self._login_time.isoformat() if self._login_time else None,
            'last_activity': self._last_activity.isoformat() if self._last_activity else None,
            'is_authenticated': self.is_authenticated()
        }
    
    def __repr__(self):
        if not self.is_authenticated():
            return "<UserSession: Not authenticated>"
        return f"<UserSession: {self._username} ({self._role})>"


# Global session instance
current_session = UserSession()


# Configuration validation on import
def validate_config():
    """Validate configuration on module import"""
    try:
        # Ensure BASE_URL is valid
        if not AppConfig.BASE_URL.startswith(('http://', 'https://')):
            raise ValueError(f"Invalid BASE_URL: {AppConfig.BASE_URL}")
        
        # Create necessary directories
        AppConfig.ensure_directories()
        
        return True
    except Exception as e:
        print(f"Configuration validation error: {e}")
        return False


# Run validation
if not validate_config():
    print("Warning: Configuration validation failed")