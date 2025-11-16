from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QMessageBox, QWidget)
from PyQt6.QtGui import QPixmap, QFont
from PyQt6.QtCore import Qt
import os
from core.database_manager import DatabaseManager
from core.activity_logger import ActivityLogger
from ui.mfa_window import MFADialog
from utils.helpers import get_feather_icon  # Use this consistently
from utils.config import AppConfig
from utils.styles import get_dialog_style  # Import styles

class LoginWindow(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.db_manager = DatabaseManager()
        self.logged_in_user = None
        self.activity_logger = ActivityLogger()  # Initialize logger

        self.setWindowTitle("Login - Inventory Management System")
        self.setFixedSize(400, 350)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)
        # Remove transparent background
        # self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Apply custom login window style with solid background
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {AppConfig.BACKGROUND_COLOR};
                border: 1px solid {AppConfig.PRIMARY_COLOR};
                border-radius: 10px;
                color: {AppConfig.TEXT_COLOR};
                font-family: {AppConfig.FONT_FAMILY};
            }}
            QLabel {{
                color: {AppConfig.TEXT_COLOR};
            }}
            QLineEdit {{
                background-color: {AppConfig.INPUT_BACKGROUND};
                border: 1px solid {AppConfig.BORDER_COLOR};
                border-radius: 5px;
                padding: 6px;
                color: {AppConfig.TEXT_COLOR};
                font-size: {AppConfig.FONT_SIZE_NORMAL}pt;
            }}
            QLineEdit:focus {{
                border: 1px solid {AppConfig.PRIMARY_COLOR};
            }}
            QPushButton {{
                background-color: {AppConfig.PRIMARY_COLOR};
                color: {AppConfig.LIGHT_TEXT};
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-size: {AppConfig.FONT_SIZE_NORMAL}pt;
            }}
            QPushButton:hover {{
                background-color: {AppConfig.SECONDARY_COLOR};
            }}
        """)
        
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(15)

        # Close button (top right)
        close_btn_layout = QHBoxLayout()
        close_btn_layout.addStretch()
        self.close_button = QPushButton()
        self.close_button.setObjectName("closeButton")
        self.close_button.setIcon(get_feather_icon("x-circle", size=20))
        self.close_button.setFixedSize(30, 30)
        self.close_button.setStyleSheet("QPushButton#closeButton { background-color: transparent; border: none; } QPushButton#closeButton:hover { background-color: rgba(255,255,255,0.1); }")
        self.close_button.clicked.connect(self.reject) # Close dialog on click
        close_btn_layout.addWidget(self.close_button)
        main_layout.addLayout(close_btn_layout)

        # Logo/Title
        logo_label = QLabel()
        logo_path = os.path.join("assets", "images", "logo.png")
        if os.path.exists(logo_path):
            pixmap = QPixmap(logo_path)
            logo_label.setPixmap(pixmap.scaled(100, 100, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation))
        else:
            logo_label.setText("IMS")
            logo_label.setFont(QFont(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_XXLARGE, QFont.Weight.Bold))
            logo_label.setStyleSheet(f"color: {AppConfig.LIGHT_TEXT};")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(logo_label)

        title_label = QLabel("Inventory Management System")
        title_label.setFont(QFont(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_LARGE, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(f"color: {AppConfig.TEXT_COLOR_ALT};")
        main_layout.addWidget(title_label)

        # Username Input
        username_layout = QHBoxLayout()
        username_icon = QLabel()
        username_icon.setPixmap(get_feather_icon("user", size=20).pixmap(20, 20))
        username_layout.addWidget(username_icon)
        
        self.username_input = QLineEdit()
        self.username_input.setPlaceholderText("Username")
        self.username_input.setClearButtonEnabled(True)
        username_layout.addWidget(self.username_input)
        main_layout.addLayout(username_layout)

        # Password Input
        password_layout = QHBoxLayout()
        password_icon = QLabel()
        password_icon.setPixmap(get_feather_icon("lock", size=20).pixmap(20, 20))
        password_layout.addWidget(password_icon)
        
        self.password_input = QLineEdit()
        self.password_input.setPlaceholderText("Password")
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.setClearButtonEnabled(True)
        self.password_input.returnPressed.connect(self.handle_login) # Trigger login on Enter
        password_layout.addWidget(self.password_input)
        main_layout.addLayout(password_layout)
        
        # Now connect username input's returnPressed after password_input is defined
        self.username_input.returnPressed.connect(self.password_input.setFocus) # Move focus to password

        # Login Button
        login_button = QPushButton("Login")
        login_button.setIcon(get_feather_icon("log-in", size=16))
        login_button.clicked.connect(self.handle_login)
        main_layout.addWidget(login_button)

        main_layout.addStretch() # Push content to top

    def handle_login(self):
        username = self.username_input.text()
        password = self.password_input.text()
        
        if not username or not password:
            QMessageBox.warning(self, "Login Error", "Please enter both username and password.")
            return
        
        # Authenticate with the database manager
        user = self.db_manager.authenticate_user(username, password)
        
        if user:
            # Check if MFA is required
            if user['role'] in ['admin', 'manager']:
                # Use MFA dialog to verify the second factor
                email = user.get('email')
                if email:
                    try:
                        from core.user_manager import UserManager
                        user_manager = UserManager()
                        
                        # Initiate MFA
                        if user_manager.initiate_mfa(user):
                            # Show MFA dialog
                            mfa_dialog = MFADialog(username=username, email=email, parent=self)
                            if mfa_dialog.exec() == QDialog.DialogCode.Accepted:
                                # MFA was successful, proceed with login
                                self.logged_in_user = user
                                
                                # Log the successful login with MFA note
                                self.activity_logger.log_activity(
                                    user_info=user,
                                    action="Logged In",
                                    target="Admin/Manager Login",
                                    details={"auth_method": "password + MFA"}
                                )
                                
                                self.login_successful()
                            else:
                                QMessageBox.warning(self, "MFA Cancelled", "Login cancelled during verification.")
                                self.password_input.clear()  # Clear password for security
                        else:
                            # If MFA initiation failed, still allow login for testing
                            QMessageBox.warning(self, "MFA Warning", 
                                            "MFA code could not be sent. Proceeding with login for testing purposes.")
                            self.logged_in_user = user
                            self.login_successful()
                    except Exception as e:
                        # If MFA has any errors, allow login for testing
                        print(f"MFA error: {str(e)}")
                        QMessageBox.warning(self, "MFA Error", 
                                        f"MFA verification error: {str(e)}. Proceeding with login for testing.")
                        self.logged_in_user = user
                        self.login_successful()
                else:
                    # If email is missing, still allow login
                    QMessageBox.warning(self, "MFA Warning", 
                                     "Email not found for MFA verification. Proceeding with login for testing.")
                    self.logged_in_user = user
                    self.login_successful()
            else:
                # No MFA required for retailers, proceed with login
                self.logged_in_user = user
                
                # Log the successful login
                self.activity_logger.log_activity(
                    user_info=user,
                    action="Logged In",
                    details={"auth_method": "password"}
                )
                
                self.login_successful()
        else:
            QMessageBox.warning(self, "Login Failed", "Invalid username or password.")

    def login_successful(self):
        """Handle successful login by creating and showing the main window"""
        try:
            from ui.main_window import MainWindow
            print(f"User logged in: {self.logged_in_user['username']} as {self.logged_in_user['role']}")
            
            # Log the successful login
            self.activity_logger.log_activity(
                user_info=self.logged_in_user,
                action="Logged In",
                target="System",
                details={"ip_address": "127.0.0.1"}  # Could be expanded to capture real IP
            )
            
            # Create and show main window
            self.main_window = MainWindow(self.logged_in_user)
            self.main_window.show()
            
            # Hide login window (don't close it yet)
            self.hide()
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"Error creating main window: {e}")
            print(error_details)
            QMessageBox.critical(self, "Application Error", 
                               f"An unexpected error occurred: {e}\n\nDetails:\n{error_details}")

    def mousePressEvent(self, event):
        # Allow dragging the window when title bar is removed
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = None

    def mouseMoveEvent(self, event):
        if not self.old_pos:
            return
        delta = event.globalPosition().toPoint() - self.old_pos
        self.move(self.pos() + delta)
        self.old_pos = event.globalPosition().toPoint()

    def get_logged_in_user(self):
        return self.logged_in_user