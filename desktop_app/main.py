"""
StockaDoodle Desktop Application - Main Entry Point
Initializes PyQt6 application and manages global state
"""
import sys
import os
import logging
import threading
from pathlib import Path
from PyQt6.QtWidgets import QApplication, QMessageBox
from PyQt6.QtCore import Qt, QTimer
from utils.styles import get_global_stylesheet
from dotenv import load_dotenv

# Import necessary UI components
from ui.login_window import LoginWindow # Assuming this file exists
from ui.main_window import MainWindow   # Assuming this file exists
# Imports for dashboard widgets are already here but are only used inside MainWindow
from ui.admin_dashboard import AdminDashboardWidget
from ui.manager_dashboard import ManagerDashboardWidget
from ui.retailer_pos import RetailerPOSWidget


# Setup logging before anything else
def setup_logging():
    """Configure application logging"""
    # Note: AppConfig must be importable for this function to work
    try:
        from utils.config import AppConfig
        log_file = Path(AppConfig.LOG_DIR) / 'stockadoodle.log'
        # Ensure log directory exists
        log_file.parent.mkdir(parents=True, exist_ok=True)
    except Exception as e:
        # Fallback if utils.config is not yet available
        log_file = Path('.') / 'stockadoodle.log'
        print(f"Warning: Could not import AppConfig. Logging to local directory. Error: {e}")

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
        
        # Main application window
        self.main_window = None


    def initialize_qt(self):
        """Initialize Qt application"""
        logger.info("Initializing Qt application")

        # Set high DPI scaling
        QApplication.setHighDpiScaleFactorRoundingPolicy(
            Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
        )

        # Create QApplication
        self.qt_app = QApplication(sys.argv)
        self.qt_app.setStyleSheet(get_global_stylesheet())
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
        from utils.config import current_session
        
        self.session = current_session

        # Setup session timeout checker
        self.session_timer = QTimer()
        self.session_timer.timeout.connect(self._check_session_timeout)
        # Check every minute (60000 ms)
        self.session_timer.start(60000)

        logger.info("Session manager initialized")

    def _check_session_timeout(self):
        """Check if session has expired and handle accordingly"""
        if self.session.is_authenticated() and self.session.is_session_expired():
            logger.warning(f"Session expired for user: {self.session.username}")

            # Notify the user via the main application window
            if self.main_window:
                self.show_error_dialog(
                    "Session Expired",
                    "Your session has expired due to inactivity. Please log in again."
                )
            
            self.handle_logout() # Clears session and navigates to login screen

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
        """Handle user logout and return to login screen."""
        if self.session.is_authenticated():
            username = self.session.username

            # Log logout activity
            self.log_desktop_action('LOGOUT', 'user', username)

            logger.info(f"User logged out: {username}")

        # Clear session
        self.session.logout()
        self.api_client.logout()

        # Navigate to login screen
        if self.main_window:
            self.main_window.show_login_screen()

    def log_desktop_action(self, action_type: str, target_entity: str, target_name: str = None):
        """
        Log desktop application activity to backend

        Args:
            action_type: Type of action (LOGIN, LOGOUT, CREATE, UPDATE, DELETE, VIEW)
            target_entity: Entity type (user, product, category, sale)
            target_name: Optional name/identifier of target
        """
        if not self.session.is_authenticated():
            # Allow 'LOGIN' action logging even if session isn't fully set up yet
            if action_type != 'LOGIN':
                 return

        try:
            # Determine user info for logging
            user_id = self.session.user_id if self.session.is_authenticated() else 'anonymous'
            username = self.session.username if self.session.is_authenticated() else target_name
            role = self.session.role if self.session.is_authenticated() else 'N/A'
            
            action_data = {
                'user_id': user_id,
                'username': username,
                'role': role,
                'action_type': action_type,
                'target_entity': target_entity,
                'target_name': target_name,
                'source': 'Desktop App'
            }

            # Send to backend (non-blocking, fire and forget)
            def send_log():
                try:
                    # _request method in StockaDoodleAPI should handle non-blocking nature
                    self.api_client._request('POST', 'log/desktop', json_data=action_data)
                except Exception as e:
                    logger.error(f"Failed to send desktop log: {e}")

            thread = threading.Thread(target=send_log, daemon=True)
            thread.start()

            logger.debug(f"Desktop action logged: {action_data}")

        except Exception as e:
            logger.error(f"Failed to log desktop action: {e}")

    def show_error_dialog(self, title: str, message: str):
        """Show error dialog to user. If MainWindow exists, set it as parent."""
        parent_widget = self.main_window if self.main_window else None
        QMessageBox.critical(parent_widget, title, message)
        logger.error(f"Error dialog shown: {title} - {message}")

    def show_info_dialog(self, title: str, message: str):
        """Show info dialog to user. If MainWindow exists, set it as parent."""
        parent_widget = self.main_window if self.main_window else None
        QMessageBox.information(parent_widget, title, message)
        logger.info(f"Info dialog shown: {title} - {message}")

    def run(self):
        """Run the application"""
        try:
            # 1. Initialize Qt environment
            self.initialize_qt()

            # 2. Initialize API Client and check connectivity
            if not self.initialize_api_client():
                self.show_error_dialog(
                    "Connection Error",
                    "Could not connect to StockaDoodle server.\nPlease ensure the API server is running."
                )
                return 1

            # 3. Initialize Session Manager
            self.initialize_session()

            # 4. Instantiate and configure the Main Application Window
            self.main_window = MainWindow(app_controller=self)
            
            # Since the application starts unauthenticated, the MainWindow
            # will automatically display the LoginWindow initially.
            self.main_window.show()

            logger.info("Application initialized successfully. Starting Qt event loop.")
            
            # 5. Start Qt event loop
            return self.qt_app.exec()

        except Exception as e:
            logger.error(f"Application crash error: {e}", exc_info=True)
            self.show_error_dialog(
                "Application Crash",
                f"An unexpected and critical error occurred:\n{str(e)}"
            )
            return 1

        finally:
            # Cleanup only logs out if still authenticated (handle_logout is safe to call)
            if self.session and self.session.is_authenticated():
                # Note: We manually call logout here instead of handle_logout to avoid 
                # attempting to switch UI when the app is shutting down.
                username = self.session.username
                self.log_desktop_action('LOGOUT', 'user', username)
                self.session.logout()
                self.api_client.logout()
            
            # Stop the session timer
            if self.session_timer:
                self.session_timer.stop()

            logger.info("Application shutdown")


def main():
    """Main entry point"""
    # Set working directory to script location
    os.chdir(Path(__file__).parent)

    # Create and run application
    app = StockaDoodleApp()
    sys.exit(app.run())


if __name__ == '__main__':
    # Ensure threading is imported for use in log_desktop_action
    import threading 
    main()