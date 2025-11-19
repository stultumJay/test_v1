from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
                             QMessageBox, QDialog, QFormLayout, QComboBox, QCheckBox, QToolButton)
from PyQt6.QtCore import Qt, QSize
from utils.config import AppConfig
from utils.decorators import role_required
from utils.style_utils import get_global_stylesheet, apply_table_styles, get_dialog_style

# NOTE: The local UserManager and ActivityLogger imports are removed.
# This class now expects an API client object for user operations.


class UserDialog(QDialog):
    """
    Dialog for adding or editing a user, now using an API client.
    """
    def __init__(self, user_client, user_data=None, parent=None):
        super().__init__(parent)
        # Store the API client for use in data submission
        self.user_client = user_client
        self.user_data = user_data
        self.password_changed = False # Track if password field was modified

        if user_data:
            self.setWindowTitle(f"Edit User: {user_data.get('username')}")
        else:
            self.setWindowTitle("Add New User")
        self.setFixedSize(400, 300)

        self.setStyleSheet(get_dialog_style())
        
        self.init_ui()
        self.load_user_data()

    def init_ui(self):
        form_layout = QFormLayout(self)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(10)

        self.username_input = QLineEdit()
        form_layout.addRow("Username:", self.username_input)

        self.password_input = QLineEdit()
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.password_input.textChanged.connect(self._password_field_changed)
        form_layout.addRow("Password:", self.password_input)
        
        # Hide password field for existing users unless they explicitly want to change it
        if self.user_data:
             self.password_input.setPlaceholderText("Leave blank to keep current password")
             self.password_input.clear() # Clear initial password hash placeholder
             self.password_input.setText("") # Ensure it starts empty

        self.email_input = QLineEdit()
        form_layout.addRow("Email (for MFA):", self.email_input)

        self.role_combo = QComboBox()
        # Data stored in QComboBox items is the internal role string
        self.role_combo.addItem("Admin", "admin")
        self.role_combo.addItem("Manager", "manager")
        self.role_combo.addItem("Retailer", "retailer")
        form_layout.addRow("Role:", self.role_combo)

        self.is_active_checkbox = QCheckBox("Account Active")
        self.is_active_checkbox.setChecked(True)
        form_layout.addRow("Status:", self.is_active_checkbox)

        button_box = QHBoxLayout()
        ok_button = QPushButton("Save")
        ok_button.setIcon(get_feather_icon("check-circle", size=16))
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.setIcon(get_feather_icon("x", size=16))
        cancel_button.clicked.connect(self.reject)
        button_box.addStretch()
        button_box.addWidget(ok_button)
        button_box.addWidget(cancel_button)
        form_layout.addRow(button_box)

    def _password_field_changed(self, text):
        """Sets a flag if the user modifies the password field."""
        # For new user, it's always considered changed if text is present.
        # For existing user, text presence indicates a change.
        if self.user_data and text:
            self.password_changed = True
        elif not self.user_data and text:
            self.password_changed = True
        elif self.user_data and not text:
            self.password_changed = False


    def load_user_data(self):
        if self.user_data:
            self.username_input.setText(self.user_data.get('username', ''))
            self.email_input.setText(self.user_data.get('email', ''))
            
            # Select the correct role in the combo box
            role = self.user_data.get('role', 'retailer')
            index = self.role_combo.findData(role)
            if index != -1:
                self.role_combo.setCurrentIndex(index)
            
            # Set active state
            is_active = self.user_data.get('is_active', True)
            self.is_active_checkbox.setChecked(is_active)
            
            # Disable username editing for existing users
            self.username_input.setReadOnly(True)
            self.username_input.setStyleSheet("background-color: #f0f0f0;")

    def get_user_data(self):
        """Collects and validates user input."""
        username = self.username_input.text().strip()
        # Only return password if it was provided/changed
        password = self.password_input.text().strip() if self.password_changed else None
        email = self.email_input.text().strip()
        role = self.role_combo.currentData()
        is_active = self.is_active_checkbox.isChecked()

        if not username:
            QMessageBox.warning(self, "Input Error", "Username cannot be empty.")
            return None
        if not self.user_data and not password:  # Password required for new users only
            QMessageBox.warning(self, "Input Error", "Password is required for new users.")
            return None
        if email and "@" not in email:
            QMessageBox.warning(self, "Input Error", "Please enter a valid email address or leave empty.")
            return None
        
        # Validation based on business rules for MFA
        if role in ['manager', 'retailer'] and not email:
            QMessageBox.warning(self, "Input Error", "Email is required for Manager and Retailer roles for MFA.")
            return None

        # When editing a user, the ID is critical for the PUT request
        data = {
            'username': username,
            'email': email if email else None,
            'role': role,
            'is_active': is_active
        }
        
        # Include the original ID if editing existing user
        if self.user_data and 'id' in self.user_data:
            data['id'] = self.user_data['id']
            
        if password:  # Only add password if it was provided/changed
            data['password'] = password
        return data


class UserManagementWidget(QWidget):
    def __init__(self, current_user, user_client, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        # Inject API client instead of local manager
        self.user_client = user_client
        # Client-side logging is removed, it is handled by the API server.

        # Apply global style instead of inline stylesheet
        self.setStyleSheet(get_global_stylesheet())
        
        self.init_ui()
        self.load_users()
        self.apply_role_permissions()

    def init_ui(self):
        """Initialize the user interface with widgets and layout."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Header and Add User Button
        header_layout = QHBoxLayout()
        title_label = QLabel("User Management")
        title_label.setFont(QFont(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_TITLE, QFont.Weight.Bold))
        title_label.setObjectName("widgetTitle")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        self.add_user_btn = QPushButton("Add New User")
        self.add_user_btn.setObjectName("addUserButton")
        self.add_user_btn.setIcon(get_feather_icon("user-plus", size=16))
        self.add_user_btn.clicked.connect(self.add_user)
        header_layout.addWidget(self.add_user_btn)
        main_layout.addLayout(header_layout)

        # Search and Filter
        search_filter_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search users by username or role...")
        self.search_input.textChanged.connect(self.filter_users)
        search_filter_layout.addWidget(self.search_input)

        self.role_filter_combo = QComboBox()
        self.role_filter_combo.addItem("All Roles", None)
        self.role_filter_combo.addItem("Admin", "admin")
        self.role_filter_combo.addItem("Manager", "manager")
        self.role_filter_combo.addItem("Retailer", "retailer")
        self.role_filter_combo.currentTextChanged.connect(self.filter_users)
        search_filter_layout.addWidget(self.role_filter_combo)
        search_filter_layout.addWidget(self.add_refresh_button())
        main_layout.addLayout(search_filter_layout)

        # User Table
        self.user_table = QTableWidget()
        self.user_table.setColumnCount(7) # ID, Username, Role, Email, Active, Created, Actions
        self.user_table.setHorizontalHeaderLabels(["ID", "Username", "Role", "Email", "Active", "Created At", "Actions"])
        apply_table_styles(self.user_table)
        main_layout.addWidget(self.user_table)

    def add_refresh_button(self):
        """Creates a refresh button."""
        refresh_button = QToolButton()
        refresh_button.setIcon(get_feather_icon("refresh-cw", size=18))
        refresh_button.clicked.connect(self.load_users)
        refresh_button.setToolTip("Refresh User List")
        refresh_button.setStyleSheet("""
            QToolButton { 
                border: none; 
                padding: 8px;
                border-radius: 8px;
            }
            QToolButton:hover {
                background-color: #e0e0e0;
            }
        """)
        return refresh_button

    @role_required(["admin"])
    def load_users(self):
        """Loads all users from the API and populates the table."""
        # API CALL: GET /users
        response = self.user_client.list()
        
        self.all_users = [] # Store all users for filtering
        self.user_table.setRowCount(0)

        if response.success:
            self.all_users = response.data
            self.filter_users() # Call filter to populate the table
        else:
            QMessageBox.critical(self, "API Error", f"Failed to load users: {response.message}")

    def filter_users(self):
        """Filters the list of users based on search and role filters."""
        search_text = self.search_input.text().lower()
        selected_role = self.role_filter_combo.currentData()

        filtered_users = []
        for user in self.all_users:
            username = user.get('username', '').lower()
            role = user.get('role', '').lower()
            
            matches_search = search_text in username or search_text in role
            matches_role = (selected_role is None) or (role == selected_role)

            if matches_search and matches_role:
                filtered_users.append(user)

        self.display_users(filtered_users)

    def display_users(self, users):
        """Populates the table with the provided list of user data."""
        self.user_table.setRowCount(len(users))
        for row, user in enumerate(users):
            # 0. ID (hidden but useful for data reference)
            id_item = QTableWidgetItem(str(user.get('id', '')))
            id_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.user_table.setItem(row, 0, id_item)

            # 1. Username
            username_item = QTableWidgetItem(user.get('username', ''))
            self.user_table.setItem(row, 1, username_item)

            # 2. Role
            role_item = QTableWidgetItem(user.get('role', '').capitalize())
            role_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.user_table.setItem(row, 2, role_item)
            
            # 3. Email
            email_item = QTableWidgetItem(user.get('email', 'N/A'))
            self.user_table.setItem(row, 3, email_item)

            # 4. Active Status
            active_item = QTableWidgetItem("Yes" if user.get('is_active') else "No")
            active_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.user_table.setItem(row, 4, active_item)
            
            # 5. Created At (Format to YYYY-MM-DD)
            created_at = user.get('created_at', '')
            date_str = created_at[:10] if created_at and len(created_at) >= 10 else created_at
            created_item = QTableWidgetItem(date_str)
            created_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.user_table.setItem(row, 5, created_item)

            # 6. Actions (Buttons)
            action_widget = QWidget()
            action_layout = QHBoxLayout(action_widget)
            action_layout.setContentsMargins(0, 0, 0, 0)
            action_layout.setSpacing(5)

            edit_btn = QPushButton()
            edit_btn.setIcon(get_feather_icon("edit", size=14))
            edit_btn.setFixedSize(QSize(30, 30))
            edit_btn.clicked.connect(lambda _, u=user: self.edit_user(u))
            action_layout.addWidget(edit_btn)

            delete_btn = QPushButton()
            delete_btn.setIcon(get_feather_icon("trash-2", size=14))
            delete_btn.setFixedSize(QSize(30, 30))
            delete_btn.clicked.connect(lambda _, u=user: self.delete_user(u))
            action_layout.addWidget(delete_btn)
            
            action_layout.addStretch()

            self.user_table.setCellWidget(row, 6, action_widget)

        self.user_table.resizeColumnsToContents()
        self.user_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)


    @role_required(["admin"])
    def add_user(self):
        """Opens a dialog to add a new user and calls the API on success."""
        dialog = UserDialog(user_client=self.user_client, user_data=None, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_user_data = dialog.get_user_data()
            if new_user_data:
                # API CALL: POST /users
                response = self.user_client.create(new_user_data)
                
                if response.success:
                    QMessageBox.information(self, "Success", f"User '{new_user_data['username']}' created successfully.")
                    # Logging is handled by the API server
                    self.load_users()
                else:
                    QMessageBox.critical(self, "API Error", f"Failed to create user: {response.message}")

    @role_required(["admin"])
    def edit_user(self, user_data):
        """Opens a dialog to edit an existing user and calls the API on success."""
        dialog = UserDialog(user_client=self.user_client, user_data=user_data, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_data = dialog.get_user_data()
            if updated_data and 'id' in updated_data:
                user_id = updated_data.pop('id')
                username = updated_data['username']

                # API CALL: PUT /users/<id>
                response = self.user_client.update(user_id, updated_data)
                
                if response.success:
                    QMessageBox.information(self, "Success", f"User '{username}' updated successfully.")
                    # Logging is handled by the API server
                    self.load_users()
                else:
                    QMessageBox.critical(self, "API Error", f"Failed to update user: {response.message}")


    @role_required(["admin"])
    def delete_user(self, user_data):
        """Prompts for confirmation and calls the API to delete a user."""
        user_id = user_data.get('id')
        username = user_data.get('username')

        reply = QMessageBox.question(self, "Confirm Delete",
                                     f"Are you sure you want to delete user '{username}' (ID: {user_id})?\\n"
                                     "This action cannot be undone.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            # API CALL: DELETE /users/<id>
            response = self.user_client.delete(user_id)
            
            if response.success:
                QMessageBox.information(self, "Success", f"User '{username}' deleted successfully.")
                # Logging is handled by the API server
                self.load_users()
            else:
                QMessageBox.critical(self, "API Error", f"Failed to delete user: {response.message}")

    def apply_role_permissions(self):
        """Adjusts UI elements based on the current user's role."""
        role = self.current_user.get('role', 'retailer')
        is_admin = role == 'admin'

        self.add_user_btn.setVisible(is_admin)

        # Disable action buttons in the table for non-admins
        for row in range(self.user_table.rowCount()):
            widget = self.user_table.cellWidget(row, 6)
            if widget:
                for btn in widget.findChildren(QPushButton):
                    btn.setEnabled(is_admin)

        if not is_admin:
            QMessageBox.information(self, "Permission Notice", 
                                    "Only Admin users can add, edit, or delete users.")