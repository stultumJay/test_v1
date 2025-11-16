# desktop_app/main.py
"""
StockaDoodle Desktop Application - Main Entry Point
Initializes PyQt6 application and manages global state
"""
import sys
import os
import logging
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt, QTimer
from dotenv import load_dotenv

# Setup logging before anything else
def setup_logging():
    """Configure application logging"""
    from utils.config import AppConfig
    
    log_file = Path(AppConfig.LOG_DIR) / 'stockadoodle.log'
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    # Set specific log levels for components
    logging.getLogger('stockadoodle.rbac').setLevel(logging.INFO)
    logging.getLogger('stockadoodle.api').setLevel(logging.DEBUG)
    
    return logging.getLogger('stockadoodle.main')


# Load environment variables
load_dotenv()

# Initialize logging
logger = setup_logging()


class StockaDoodleApp:
    """
    Main application controller
    Manages global state, API client, and session
    """
    
    def __init__(self):
        """Initialize application components"""
        logger.info("Initializing StockaDoodle Desktop Application")
        
        # Qt Application instance
        self.qt_app = None
        
        # API Client instance
        self.api_client = None
        
        # Session manager
        self.session = None
        
        # Session timeout checker
        self.session_timer = None
    
    def initialize_qt(self):
        """Initialize Qt application"""
        logger.info("Initializing Qt application")
        
        # Set high DPI scaling
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )
        
        # Create QApplication
        self.qt_app = QApplication(sys.argv)
        self.qt_app.setApplicationName("StockaDoodle IMS")
        self.qt_app.setApplicationVersion("1.0.0")
        
        # Set application style
        self.qt_app.setStyle('Fusion')  # Modern cross-platform style
        
        logger.info("Qt application initialized")
    
    def initialize_api_client(self):
        """Initialize API client for backend communication"""
        from api_client.stockadoodle_api import StockaDoodleAPI
        from utils.config import AppConfig
        
        logger.info(f"Initializing API client with base URL: {AppConfig.BASE_URL}")
        
        try:
            self.api_client = StockaDoodleAPI(
                base_url=AppConfig.BASE_URL,
                timeout=AppConfig.API_TIMEOUT
            )
            
            # Test connection
            health_resp = self.api_client._request('GET', 'health')
            if health_resp.success:
                logger.info("API connection successful")
                return True
            else:
                logger.error(f"API health check failed: {health_resp.error}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to initialize API client: {e}")
            return False
    
    def initialize_session(self):
        """Initialize session manager"""
        from utils.config import current_session, AppConfig
        
        self.session = current_session
        
        # Setup session timeout checker
        self.session_timer = QTimer()
        self.session_timer.timeout.connect(self._check_session_timeout)
        # Check every minute
        self.session_timer.start(60000)
        
        logger.info("Session manager initialized")
    
    def _check_session_timeout(self):
        """Check if session has expired and handle accordingly"""
        if self.session.is_authenticated() and self.session.is_session_expired():
            logger.warning(f"Session expired for user: {self.session.username}")
            
            # TODO: Show session expired dialog when UI is implemented
            # For now, just logout
            self.handle_logout()
    
    def handle_login(self, username: str, password: str) -> bool:
        """
        Handle user login
        
        Args:
            username: User's username
            password: User's password
            
        Returns:
            True if login successful, False otherwise
        """
        logger.info(f"Login attempt for user: {username}")
        
        try:
            # Authenticate via API
            resp = self.api_client.login(username, password)
            
            if resp.success:
                # Store session
                self.session.login(resp.data)
                logger.info(f"Login successful for {username} ({self.session.role})")
                
                # Log login activity
                self.log_desktop_action('LOGIN', 'user', username)
                
                return True
            else:
                logger.warning(f"Login failed for {username}: {resp.error}")
                return False
                
        except Exception as e:
            logger.error(f"Login error: {e}")
            return False
    
    def handle_logout(self):
        """Handle user logout"""
        if self.session.is_authenticated():
            username = self.session.username
            
            # Log logout activity
            self.log_desktop_action('LOGOUT', 'user', username)
            
            logger.info(f"User logged out: {username}")
        
        # Clear session
        self.session.logout()
        self.api_client.logout()
        
        # TODO: Navigate to login screen when UI is implemented
    
    def log_desktop_action(self, action_type: str, target_entity: str, target_name: str = None):
        """
        Log desktop application activity to backend
        
        Args:
            action_type: Type of action (LOGIN, LOGOUT, CREATE, UPDATE, DELETE, VIEW)
            target_entity: Entity type (user, product, category, sale)
            target_name: Optional name/identifier of target
        """
        if not self.session.is_authenticated():
            return
        
        try:
            action_data = {
                'user_id': self.session.user_id,
                'username': self.session.username,
                'role': self.session.role,
                'action_type': action_type,
                'target_entity': target_entity,
                'target_name': target_name,
                'source': 'Desktop App'
            }
            
            # Send to backend (non-blocking, fire and forget)
            # Use separate thread to avoid blocking UI
            import threading
            def send_log():
                try:
                    self.api_client._request('POST', 'log/desktop', json_data=action_data)
                except Exception as e:
                    logger.error(f"Failed to send desktop log: {e}")
            
            thread = threading.Thread(target=send_log, daemon=True)
            thread.start()
            
            logger.debug(f"Desktop action logged: {action_data}")
            
        except Exception as e:
            logger.error(f"Failed to log desktop action: {e}")
    
    def show_error_dialog(self, title: str, message: str):
        """Show error dialog to user"""
        QMessageBox.critical(None, title, message)
        logger.error(f"Error dialog shown: {title} - {message}")
    
    def show_info_dialog(self, title: str, message: str):
        """Show info dialog to user"""
        QMessageBox.information(None, title, message)
        logger.info(f"Info dialog shown: {title} - {message}")
    
    def run(self):
        """Run the application"""
        try:
            # Initialize components
            self.initialize_qt()
            
            if not self.initialize_api_client():
                self.show_error_dialog(
                    "Connection Error",
                    "Could not connect to StockaDoodle server.\n"
                    "Please ensure the API server is running."
                )
                return 1
            
            self.initialize_session()
            
            # TODO: Show login window when UI is implemented
            # For now, show a placeholder
            logger.info("Application initialized successfully")
            logger.info("TODO: Implement login window")
            
            # Test login (remove when UI is ready)
            if self.handle_login('admin', 'admin'):
                logger.info("Test login successful")
                logger.info(f"Session: {self.session}")
            
            # Start Qt event loop
            # return self.qt_app.exec()
            
            # For now, exit immediately
            logger.info("Application would start Qt event loop here")
            return 0
            
        except Exception as e:
            logger.error(f"Application error: {e}", exc_info=True)
            self.show_error_dialog(
                "Application Error",
                f"An unexpected error occurred:\n{str(e)}"
            )
            return 1
        
        finally:
            # Cleanup
            if self.session and self.session.is_authenticated():
                self.handle_logout()
            
            logger.info("Application shutdown")


def main():
    """Main entry point"""
    # Set working directory to script location
    os.chdir(Path(__file__).parent)
    
    # Create and run application
    app = StockaDoodleApp()
    sys.exit(app.run())


if __name__ == '__main__':
    main()