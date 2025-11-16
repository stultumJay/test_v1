from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, 
    QFrame, QWidget, QGridLayout
)
from PyQt6.QtCore import Qt, QSize, QTimer
from PyQt6.QtGui import QPixmap, QImage, QFont
from typing import Dict, Any

from api_client.stockadoodle_api import API
from utils.config import AppConfig, SESSION
from utils.styles import get_global_stylesheet, show_error_message, show_success_message
from utils.helpers import get_feather_icon

class MFAWindow(QDialog):
    """
    Handles Multi-Factor Authentication (MFA) for Admin and Manager roles.
    Integrates with api.mfa.send_code() and api.mfa.verify_code().
    """
    def __init__(self, user_data: Dict[str, Any], pre_mfa_token: str, login_window: QWidget, parent=None):
        super().__init__(parent)
        self.user_data = user_data
        self.pre_mfa_token = pre_mfa_token # Token received after login, before MFA
        self.login_window = login_window
        
        self.setWindowTitle("MFA Verification")
        self.setFixedSize(400, 500)
        self.setStyleSheet(get_global_stylesheet())
        
        self.setup_ui()
        self.send_mfa_code()

    def setup_ui(self):
        """Builds the central card for MFA verification."""
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        mfa_card = QFrame(self)
        mfa_card.setObjectName("Card")
        mfa_card.setStyleSheet(AppConfig.get_global_stylesheet() + f"""
            QFrame#Card {{
                background-color: {AppConfig.CARD_BACKGROUND};
                min-width: 350px;
                padding: 30px;
                border-radius: {AppConfig.BORDER_RADIUS};
            }}
        """)
        
        card_layout = QVBoxLayout(mfa_card)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter | Qt.AlignmentFlag.AlignTop)
        
        # Icon/Header
        icon_label = QLabel()
        icon_label.setPixmap(get_feather_icon("lock", AppConfig.PRIMARY_COLOR, 64).pixmap(QSize(64, 64)))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(icon_label)
        
        title_label = QLabel("Two-Factor Authentication")
        title_label.setObjectName("Header")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(title_label)
        
        # Email instruction
        email_label = QLabel(f"A verification code has been sent to your email: {self.user_data.get('email', 'N/A')}.")
        email_label.setWordWrap(True)
        email_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        email_label.setStyleSheet(f"color: {AppConfig.TEXT_MUTED}; margin-top: 10px; margin-bottom: 20px;")
        card_layout.addWidget(email_label)

        # Code Input
        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Enter 6-digit Code (Mock: 123456)")
        self.code_input.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.code_input.setMaxLength(6)
        card_layout.addWidget(self.code_input)

        # Verify Button
        self.verify_button = QPushButton("VERIFY CODE")
        self.verify_button.clicked.connect(self.verify_mfa_code)
        card_layout.addWidget(self.verify_button)
        
        # Resend Button
        self.resend_button = QPushButton("Resend Code")
        self.resend_button.clicked.connect(self.send_mfa_code)
        self.resend_button.setStyleSheet(f"background-color: transparent; color: {AppConfig.TEXT_MUTED}; border: none;")
        card_layout.addWidget(self.resend_button)
        
        card_layout.addStretch(1)

        # Back to Login Button
        back_button = QPushButton("Back to Login")
        back_button.clicked.connect(self.close)
        back_button.setStyleSheet(f"background-color: transparent; color: {AppConfig.DANGER_COLOR}; border: none;")
        card_layout.addWidget(back_button)
        
        main_layout.addWidget(mfa_card)
        
        # Note: QR code/Backup code UI is complex. For brevity, we focus on the core email verification flow.

    def send_mfa_code(self):
        """
        Calls the API to send the MFA code.
        """
        self.resend_button.setText("Sending...")
        self.resend_button.setEnabled(False)
        
        user_id = self.user_data['id']
        email = self.user_data['email']
        
        # --- API Integration Point 2: send_code ---
        resp = API.mfa.send_code(user_id, email)
        
        if resp.success:
            show_success_message("Code Sent", resp.data.get('message', "MFA code has been sent to your email."), self)
        else:
            show_error_message("MFA Error", resp.error or "Failed to send MFA code.", self)

        # Re-enable resend button after a short delay
        QTimer.singleShot(5000, lambda: self.resend_button.setText("Resend Code"))
        QTimer.singleShot(5000, lambda: self.resend_button.setEnabled(True))
        
    def verify_mfa_code(self):
        """
        Calls the API to verify the entered MFA code.
        """
        code = self.code_input.text().strip()
        if len(code) != 6 or not code.isdigit():
            show_error_message("Invalid Code", "Please enter the 6-digit numeric code.", self)
            return

        self.verify_button.setText("Verifying...")
        self.verify_button.setEnabled(False)
        
        user_id = self.user_data['id']
        
        # --- API Integration Point 3: verify_code ---
        resp = API.mfa.verify_code(user_id, code)
        
        self.verify_button.setText("VERIFY CODE")
        self.verify_button.setEnabled(True)
        
        if resp.success and resp.data.get('is_verified'):
            final_token = resp.data['token']
            
            # Finalize session using the verified token
            SESSION.login(self.user_data, final_token)
            
            show_success_message("MFA Successful", "Verification complete. Welcome!", self)
            
            # Delegate opening the main window back to the login window
            if self.login_window:
                self.login_window.handle_mfa_success()
            self.accept() # Close the dialog
        else:
            show_error_message("Verification Failed", resp.error or "The code is incorrect or expired.", self)

    def closeEvent(self, event):
        """Handle close event to return to login screen."""
        if self.login_window and not SESSION.is_logged_in():
            self.login_window.show()
        super().closeEvent(event)