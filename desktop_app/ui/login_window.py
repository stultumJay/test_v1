from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, 
    QPushButton, QCheckBox, QFrame, QMessageBox, QApplication
)
from PyQt6.QtGui import QFont, QIcon
from PyQt6.QtCore import Qt, QSize, QTimer

from ui.mfa_window import MFAWindow
from ui.main_window import MainWindow
from api_client.stockadoodle_api import API
from utils.config import AppConfig, SESSION
from utils.styles import get_global_stylesheet, show_error_message
from utils.helpers import get_feather_icon

class LoginWindow(QMainWindow):
    """
    The main login window for StockaDoodle. Handles API authentication 
    and session management.
    """
    def __init__(self):
        super().__init__()
        self.setWindowTitle("StockaDoodle - Login")
        self.setGeometry(100, 100, 450, 600)
        self.setFixedSize(450, 600) # Fixed size for a modern login screen
        
        self.setStyleSheet(get_global_stylesheet())
        
        self.main_window = None
        self.mfa_window = None
        
        self.setup_ui()
        self.check_saved_session()
        self.load_remembered_user()

    def setup_ui(self):
        """Builds the central login card and layout."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_layout = QVBoxLayout(central_widget)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # --- Login Card ---
        login_card = QFrame(self)
        login_card.setObjectName("Card")
        login_card.setStyleSheet(get_global_stylesheet() + f"""
            QFrame#Card {{
                background-color: {AppConfig.CARD_BACKGROUND};
                min-width: 350px;
                padding: 30px;
                border-radius: {AppConfig.BORDER_RADIUS};
            }}
        """)
        
        card_layout = QVBoxLayout(login_card)
        card_layout.setSpacing(20)
        
        # Logo/Title
        title_label = QLabel("StockaDoodle")
        title_label.setObjectName("Title")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(title_label)
        
        subtitle_label = QLabel("Inventory Management System")
        subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_label.setStyleSheet(f"color: {AppConfig.TEXT_MUTED};")
        card_layout.addWidget(subtitle_label)
        
        # Username Input
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setClearButtonEnabled(True)
        self.username_input.setStyleSheet("padding-left: 30px;")
        self.username_input.setTextMargins(30, 0, 0, 0) # Add left margin for icon
        self.username_input.setText("admin") # Pre-fill for testing
        card_layout.addWidget(self.username_input)

        # Password Input
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setClearButtonEnabled(True)
        self.password_input.setStyleSheet("padding-left: 30px;")
        self.password_input.setTextMargins(30, 0, 0, 0) # Add left margin for icon
        self.password_input.setText("admin") # Pre-fill for testing
        card_layout.addWidget(self.password_input)
        
        # Add icons to inputs
        self._add_input_icon(self.username_input, get_feather_icon("user", AppConfig.TEXT_MUTED, 18))
        self._add_input_icon(self.password_input, get_feather_icon("lock", AppConfig.TEXT_MUTED, 18))

        # Remember Me and Forgot Password (Placeholder)
        remember_layout = QHBoxLayout()
        self.remember_me_check = QCheckBox("Remember Me")
        self.remember_me_check.setStyleSheet(f"color: {AppConfig.TEXT_MUTED};")
        remember_layout.addWidget(self.remember_me_check)
        remember_layout.addStretch(1)
        
        forgot_pass = QLabel("Forgot Password?")
        forgot_pass.setStyleSheet(f"color: {AppConfig.PRIMARY_COLOR}; cursor: pointer;")
        remember_layout.addWidget(forgot_pass) # Placeholder functionality
        card_layout.addLayout(remember_layout)
        
        # Login Button
        self.login_button = QPushButton("LOG IN")
        self.login_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.login_button.clicked.connect(self.authenticate)
        card_layout.addWidget(self.login_button)
        
        main_layout.addWidget(login_card)

    def _add_input_icon(self, line_edit: QLineEdit, icon: QIcon):
        """Sets an icon inside a QLineEdit for a nicer look."""
        action = line_edit.addAction(icon, QLineEdit.ActionPosition.LeadingPosition)
        action.setVisible(True)

    def load_remembered_user(self):
        """Loads username and 'remember me' state from config."""
        config = AppConfig.load_config()
        if config['remember_me']:
            self.remember_me_check.setChecked(True)
            self.username_input.setText(config['last_username'])
            self.password_input.setFocus() # Focus password field

    def check_saved_session(self):
        """Checks for an active session on startup."""
        if SESSION.is_logged_in():
            QTimer.singleShot(100, self.open_main_window) # Delay slightly to allow UI to draw

    def authenticate(self):
        """
        Handles the login process, replacing DatabaseManager with API client.
        """
        username = self.username_input.text().strip()
        password = self.password_input.text()
        
        if not username or not password:
            show_error_message("Login Failed", "Please enter both username and password.", self)
            return

        self.login_button.setText("Logging In...")
        self.login_button.setEnabled(False)
        
        # --- API Integration Point 1: auth_login ---
        resp = API.users.auth_login(username, password)
        
        self.login_button.setText("LOG IN")
        self.login_button.setEnabled(True)
        
        if resp.success:
            user_data = resp.data['user']
            token = resp.data['token']
            
            # Save remember me state
            AppConfig.save_config(self.remember_me_check.isChecked(), username if self.remember_me_check.isChecked() else "")

            # Check for MFA requirement
            if user_data['role'] in ['Admin', 'Manager']:
                self.open_mfa_window(user_data, token)
            else:
                # Retailers log in directly
                SESSION.login(user_data, token)
                self.open_main_window()
        else:
            show_error_message("Login Failed", resp.error or "An unknown login error occurred.", self)

    def open_mfa_window(self, user_data: Dict[str, Any], token: str):
        """Opens the MFA window for Admin/Manager roles."""
        self.hide()
        self.mfa_window = MFAWindow(user_data, token, self)
        self.mfa_window.show()

    def open_main_window(self):
        """Opens the main application window."""
        self.hide()
        # Pass the API client directly to MainWindow
        self.main_window = MainWindow(api_client=API)
        self.main_window.show()

    def handle_mfa_success(self):
        """Called by MFAWindow upon successful verification."""
        self.open_main_window()
        if self.mfa_window:
            self.mfa_window.close()
            self.mfa_window = None

    def handle_logout(self):
        """Handles session cleanup and returns to login screen."""
        SESSION.logout()
        if self.main_window:
            self.main_window.close()
            self.main_window = None
        
        self.password_input.clear()
        self.show()