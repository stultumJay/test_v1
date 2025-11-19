from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, 
    QLabel, QLineEdit, QPushButton, QGroupBox, 
    QMessageBox, QSpacerItem, QSizePolicy
)
from PyQt6.QtCore import Qt, pyqtSignal, QLocale
from PyQt6.QtGui import QFont, QIcon
from typing import TYPE_CHECKING, Dict, Any

# Type checking import for better IDE support, assumes API client location
if TYPE_CHECKING:
    from api_client.enhanced_clients import StockadoodleApiClient

class UserProfileTab(QWidget):
    """
    A dedicated tab for viewing and updating the current user's profile
    information and managing security settings (Password, MFA).
    """
    
    # Custom signal to notify when user data might have changed (e.g., role)
    profile_updated = pyqtSignal()

    def __init__(self, api_client: 'StockadoodleApiClient', user_data: Dict[str, Any], parent=None):
        super().__init__(parent)
        self.api_client = api_client
        self.user_data = user_data  # Initial data passed from login/dashboard
        self._is_loading = False

        self._setup_ui()
        self.load_profile_data()

    def _setup_ui(self):
        """Initializes the main layout and widgets."""
        main_layout = QVBoxLayout(self)
        main_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # --- Header ---
        header_label = QLabel("👤 User Profile")
        header_label.setObjectName("HeaderLabel") # For potential CSS styling
        header_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        main_layout.addWidget(header_label)
        
        # --- Profile Group Box ---
        profile_group = QGroupBox("User Details")
        profile_group.setFont(QFont("Arial", 12))
        profile_layout = QFormLayout(profile_group)
        profile_layout.setContentsMargins(15, 20, 15, 15)
        profile_layout.setSpacing(15)

        # Read-Only Fields
        self.user_id_label = self._create_read_only_field(profile_layout, "User ID:")
        self.username_label = self._create_read_only_field(profile_layout, "Username:")
        self.role_label = self._create_read_only_field(profile_layout, "Role:")
        self.mfa_status_label = self._create_read_only_field(profile_layout, "MFA Status:")

        # Editable Fields
        self.full_name_input = QLineEdit()
        profile_layout.addRow("Full Name:", self.full_name_input)
        
        self.email_input = QLineEdit()
        profile_layout.addRow("Email:", self.email_input)
        
        # Save Button
        self.save_button = QPushButton("💾 Save Profile Changes")
        self.save_button.clicked.connect(self._save_profile)
        profile_layout.addRow(self.save_button)
        
        main_layout.addWidget(profile_group)

        # --- Security Group Box ---
        security_group = QGroupBox("Security Actions")
        security_group.setFont(QFont("Arial", 12))
        security_layout = QHBoxLayout(security_group)
        
        self.change_password_btn = QPushButton("🔑 Change Password")
        self.change_password_btn.clicked.connect(self._open_change_password_dialog)
        
        self.manage_mfa_btn = QPushButton("🛡️ Manage MFA")
        self.manage_mfa_btn.clicked.connect(self._open_mfa_management_dialog)
        
        security_layout.addWidget(self.change_password_btn)
        security_layout.addWidget(self.manage_mfa_btn)
        
        main_layout.addWidget(security_group)

        # Add vertical stretch to push content to the top
        main_layout.addItem(QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

    def _create_read_only_field(self, layout: QFormLayout, label_text: str) -> QLabel:
        """Helper to create a read-only label pair in the form layout."""
        value_label = QLabel("Loading...")
        # Style the value label to look distinct from inputs
        value_label.setStyleSheet("QLabel { color: #555; font-weight: 500; padding: 2px; }")
        
        label = QLabel(label_text)
        label.setFont(QFont("Arial", 10, QFont.Weight.Bold))
        
        layout.addRow(label, value_label)
        return value_label
        
    def load_profile_data(self):
        """Fetches the current user's profile data from the API and updates UI."""
        if self._is_loading: return
        self._is_loading = True
        
        # Use QLocale for formatting if necessary (e.g., currency, dates)
        # Not strictly needed for a profile, but good practice.
        # locale = QLocale() 
        
        try:
            # Assumes API client has a method to get the current user's data
            # Use the user ID from the initial data passed to the tab
            user_data = self.api_client.get_user_profile(user_id=self.user_data['user_id'])
            
            # Update internal data
            self.user_data.update(user_data) 

            # Update read-only fields
            self.user_id_label.setText(user_data.get('user_id', 'N/A'))
            self.username_label.setText(user_data.get('username', 'N/A'))
            self.role_label.setText(user_data.get('role', 'N/A').capitalize())
            
            mfa_status = "✅ Enabled" if user_data.get('mfa_enabled', False) else "❌ Disabled"
            self.mfa_status_label.setText(mfa_status)
            
            # Populate editable fields
            self.full_name_input.setText(user_data.get('full_name', ''))
            self.email_input.setText(user_data.get('email', ''))

        except Exception as e:
            QMessageBox.critical(self, "API Error", f"Failed to load user profile: {e}")
        finally:
            self._is_loading = False

    def _save_profile(self):
        """Updates the user's profile with the new full name and email via API."""
        new_full_name = self.full_name_input.text().strip()
        new_email = self.email_input.text().strip()
        
        if not new_full_name or not new_email:
            QMessageBox.warning(self, "Input Error", "Full Name and Email cannot be empty.")
            return

        new_data = {
            'full_name': new_full_name,
            'email': new_email
        }
        
        try:
            # Assumes the API supports partial updates via this method
            self.api_client.update_user_profile(user_id=self.user_data['user_id'], data=new_data)
            QMessageBox.information(self, "Success", "Profile updated successfully!")
            
            # Reload data to ensure UI reflects the latest state from the server
            self.load_profile_data()
            self.profile_updated.emit() # Signal any dashboard that needs to react

        except Exception as e:
            QMessageBox.critical(self, "Update Error", f"Failed to update profile: {e}")

    def _open_change_password_dialog(self):
        """Placeholder for opening a modal dialog to change the password."""
        # In a full app, this would open a custom QDialog for password change
        QMessageBox.information(self, "Action Required", "Launching Change Password dialog...")
        # Implementation would involve a new dialog class, e.g., ChangePasswordDialog(self.api_client)

    def _open_mfa_management_dialog(self):
        """Placeholder for opening a modal dialog to manage MFA settings."""
        # In a full app, this would open a custom QDialog for MFA setup/disable
        QMessageBox.information(self, "Action Required", "Launching MFA Management dialog...")
        # Implementation would involve a new dialog class, e.g., MfaManagementDialog(self.api_client)