import random
import string
from PyQt6.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QMessageBox)
from PyQt6.QtGui import QFont
from PyQt6.QtCore import Qt
from utils.helpers import get_feather_icon
from core.mfa_service import MFAService
from utils.config import AppConfig
from utils.styles import get_dialog_style  # Import styles

class MFADialog(QDialog):
    def __init__(self, username, email=None, parent=None):
        super().__init__(parent)
        self.username = username
        self.email = email or f"{username}@example.com"
        self.mfa_code = ""
        
        self.mfa_service = MFAService()
        self.mfa_service.send_mfa_code(self.email, self.username)

        self.setWindowTitle("Two-Factor Authentication")
        self.setFixedSize(400, 300)
        
        # Apply dialog style
        self.setStyleSheet(get_dialog_style())
        
        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(30, 30, 30, 30)
        main_layout.setSpacing(15)

        title_label = QLabel("Two-Factor Authentication")
        title_label.setFont(QFont(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_LARGE, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet(f"color: {AppConfig.LIGHT_TEXT};")
        main_layout.addWidget(title_label)

        info_label = QLabel(f"A verification code has been sent to {self.mask_email(self.email)}.")
        info_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_label.setWordWrap(True)
        info_label.setStyleSheet(f"color: {AppConfig.TEXT_COLOR_ALT};")
        main_layout.addWidget(info_label)

        code_layout = QHBoxLayout()
        code_icon = QLabel()
        code_icon.setPixmap(get_feather_icon("key", size=20).pixmap(20, 20))
        code_layout.addWidget(code_icon)

        self.code_input = QLineEdit()
        self.code_input.setPlaceholderText("Enter verification code")
        self.code_input.returnPressed.connect(self.verify_code)
        code_layout.addWidget(self.code_input)
        main_layout.addLayout(code_layout)

        # Buttons layout
        buttons_layout = QHBoxLayout()
        buttons_layout.addStretch()
        
        verify_button = QPushButton("Verify Code")
        verify_button.setObjectName("verifyButton")
        verify_button.setIcon(get_feather_icon("check-circle", size=16))
        verify_button.clicked.connect(self.verify_code)
        buttons_layout.addWidget(verify_button)
        
        main_layout.addLayout(buttons_layout)
        main_layout.addStretch()

    def verify_code(self):
        entered_code = self.code_input.text().strip()
        
        if not entered_code:
            QMessageBox.warning(self, "Verification Error", "Please enter the verification code.")
            return
        
        # Verify code with MFA service
        if self.mfa_service.verify_mfa_code(self.username, entered_code):
            # Code verified successfully
            self.accept()
        else:
            QMessageBox.warning(self, "Verification Failed", "Invalid verification code. Please try again.")
            self.code_input.clear()
            self.code_input.setFocus()

    def get_code(self):
        return self.mfa_code

    def mask_email(self, email):
        """Mask the email for privacy, showing only first and last characters."""
        if not email or '@' not in email:
            return email
        
        parts = email.split('@')
        user_part = parts[0]
        domain_part = parts[1]
        
        # Mask user part (show first 2 chars and last char)
        if len(user_part) > 3:
            user_masked = f"{user_part[:2]}{'*' * (len(user_part) - 3)}{user_part[-1]}"
        else:
            user_masked = user_part  # Don't mask if too short
            
        return f"{user_masked}@{domain_part}"

    def mousePressEvent(self, event):
        # Allow dragging the window when title bar is removed
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = event.globalPosition().toPoint()

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            self.old_pos = None

    def mouseMoveEvent(self, event):
        if not hasattr(self, 'old_pos') or not self.old_pos:
            return
        delta = event.globalPosition().toPoint() - self.old_pos
        self.move(self.pos() + delta)
        self.old_pos = event.globalPosition().toPoint()