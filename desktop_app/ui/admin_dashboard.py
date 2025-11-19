import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QPushButton, QLineEdit,
    QComboBox, QFrame, QSizePolicy, QHeaderView, QToolButton,
    QGridLayout, QSpacerItem, QScrollArea, QDialog
)
from PyQt6.QtGui import QFont, QIcon, QPixmap
from PyQt6.QtCore import Qt, QSize, QTimer

from typing import Dict, Any, List

from api_client.stockadoodle_api import StockaDoodleAPI, MOCK_USERS
from utils.config import AppConfig, SESSION
from utils.styles import apply_table_styles, get_dashboard_card_style, show_error_message, show_success_message
from utils.helpers import get_feather_icon, format_date

# --- Custom Table Cell Widgets ---

class BadgeLabel(QLabel):
    """A custom QLabel for displaying role or status as a colored badge."""
    def __init__(self, text: str, badge_type: str):
        super().__init__(text)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedSize(80, 24)
        
        # Define colors based on type
        colors = {
            "Admin": AppConfig.DANGER_COLOR,
            "Manager": AppConfig.PRIMARY_COLOR,
            "Retailer": AppConfig.SUCCESS_COLOR,
            "Active": AppConfig.SUCCESS_COLOR,
            "Inactive": AppConfig.DANGER_COLOR,
            "Desktop App": "#64B5F6", # Light Blue
            "Postman": "#FFB74D", # Amber
        }
        
        bg_color = colors.get(badge_type, AppConfig.TEXT_MUTED)
        
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color};
                color: white;
                border-radius: 12px;
                padding: 4px;
                font-weight: bold;
                font-size: 8pt;
            }}
        """)

class NameCellWidget(QWidget):
    """A custom widget to display avatar + username in a table cell."""
    def __init__(self, user_data: Dict[str, Any]):
        super().__init__()
        h_layout = QHBoxLayout(self)
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.Center)
        
        # Avatar (Placeholder)
        avatar_label = QLabel()
        avatar_label.setPixmap(get_feather_icon("user", "white", 24).pixmap(QSize(24, 24)))
        avatar_label.setFixedSize(28, 28)
        avatar_label.setStyleSheet(f"border-radius: 14px; background-color: {AppConfig.PRIMARY_COLOR};")
        
        # Text
        text_v_layout = QVBoxLayout()
        text_v_layout.setContentsMargins(0, 0, 0, 0)
        text_v_layout.setSpacing(0)
        
        username_label = QLabel(user_data.get('username', 'N/A'))
        username_label.setFont(QFont(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_NORMAL + 1, QFont.Weight.Bold))
        username_label.setStyleSheet(f"color: {AppConfig.TEXT_DEFAULT};")
        
        role_label = QLabel(user_data.get('role', 'N/A'))
        role_label.setStyleSheet(f"color: {AppConfig.TEXT_MUTED}; font-size: 8pt;")
        
        text_v_layout.addWidget(username_label)
        text_v_layout.addWidget(role_label)
        
        h_layout.addWidget(avatar_label)
        h_layout.addSpacing(10)
        h_layout.addLayout(text_v_layout)
        h_layout.addStretch(1)

class ActionButtonsWidget(QWidget):
    """A widget containing edit, permissions, and delete buttons."""
    def __init__(self, user_id: int, on_edit, on_delete):
        super().__init__()
        h_layout = QHBoxLayout(self)
        h_layout.setContentsMargins(5, 0, 5, 0)
        h_layout.setSpacing(5)
        
        # Edit Button
        edit_btn = QToolButton()
        edit_btn.setIcon(get_feather_icon("edit-3", AppConfig.TEXT_MUTED, 16))
        edit_btn.setToolTip("Edit User")
        edit_btn.clicked.connect(lambda: on_edit(user_id))
        
        # Delete Button
        delete_btn = QToolButton()
        delete_btn.setIcon(get_feather_icon("trash-2", AppConfig.DANGER_COLOR, 16))
        delete_btn.setToolTip("Delete User")
        delete_btn.clicked.connect(lambda: on_delete(user_id))

        # Apply common style
        style = "QToolButton { border: none; padding: 5px; border-radius: 5px;}"
        style += "QToolButton:hover { background-color: #333333; }"
        edit_btn.setStyleSheet(style)
        delete_btn.setStyleSheet(style)
        
        h_layout.addWidget(edit_btn)
        h_layout.addWidget(delete_btn)
        h_layout.addStretch(1)

# --- Admin Dashboard Widget ---

class UserManagementWidget(QWidget):
    """The main user management view for the Admin role."""
    def __init__(self, api_client: StockaDoodleAPI):
        super().__init__()
        self.api = api_client
        self.current_user = self.api.session.user_data # Get user data from session
        self.all_users: List[Dict[str, Any]] = []

        self.setup_ui()
        self.load_users()

    def setup_ui(self):
        """Sets up the layout for user management."""
        v_layout = QVBoxLayout(self)
        v_layout.setContentsMargins(20, 20, 20, 20)
        v_layout.setSpacing(15)

        # Header and Actions
        header_h_layout = QHBoxLayout()
        header_h_layout.setSpacing(10)

        header_label = QLabel("User Management")
        header_label.setObjectName("Header")
        header_h_layout.addWidget(header_label)

        header_h_layout.addStretch(1)

        # Search and Filter
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by Username or Role...")
        self.search_input.setFixedWidth(250)
        self.search_input.textChanged.connect(self.filter_users)
        header_h_layout.addWidget(self.search_input)

        self.filter_combo = QComboBox()
        self.filter_combo.addItems(["All Roles", "Admin", "Manager", "Retailer"])
        self.filter_combo.setFixedWidth(120)
        self.filter_combo.currentIndexChanged.connect(self.filter_users)
        header_h_layout.addWidget(self.filter_combo)

        # Add User Button
        self.add_user_btn = QPushButton(get_feather_icon("plus", "white", 16), "Add New User")
        self.add_user_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_user_btn.clicked.connect(self.add_new_user)
        header_h_layout.addWidget(self.add_user_btn)

        v_layout.addLayout(header_h_layout)

        # User Table
        self.user_table = QTableWidget()
        self.user_table.setColumnCount(6)
        self.user_table.setHorizontalHeaderLabels(["ID", "User", "Role", "Status", "Created At", "Actions"])
        self.user_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.user_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.user_table.verticalHeader().setVisible(False)
        
        apply_table_styles(self.user_table)
        
        # Stretch columns
        header = self.user_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed)
        self.user_table.setColumnWidth(5, 120)

        v_layout.addWidget(self.user_table)

    def load_users(self):
        """Fetches user data from the API and populates the table."""
        self.user_table.setRowCount(0) # Clear existing rows
        
        # --- API Integration Point 4: users.list() ---
        resp = self.api.users.list()

        if resp.success:
            self.all_users = resp.data
            self.populate_table(self.all_users)
        else:
            self.all_users = []
            show_error_message("Data Error", f"Failed to load users: {resp.error}", self)

    def populate_table(self, users: List[Dict[str, Any]]):
        """Fills the QTableWidget with user data."""
        self.user_table.setRowCount(len(users))
        
        for row, user in enumerate(users):
            # 0. ID
            item_id = QTableWidgetItem(str(user.get('id', 'N/A')))
            item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.user_table.setItem(row, 0, item_id)
            
            # 1. User (NameCellWidget)
            name_widget = NameCellWidget(user)
            self.user_table.setCellWidget(row, 1, name_widget)

            # 2. Role (BadgeLabel)
            role_badge = BadgeLabel(user.get('role', 'N/A'), user.get('role', ''))
            self.user_table.setCellWidget(row, 2, role_badge)

            # 3. Status (BadgeLabel)
            status_text = "Active" if user.get('is_active') else "Inactive"
            status_badge = BadgeLabel(status_text, status_text)
            self.user_table.setCellWidget(row, 3, status_badge)
            
            # 4. Created At
            created_at_str = user.get('created_at', 'N/A')
            item_created = QTableWidgetItem(format_date(created_at_str))
            self.user_table.setItem(row, 4, item_created)

            # 5. Actions (ActionButtonsWidget)
            actions_widget = ActionButtonsWidget(
                user_id=user['id'],
                on_edit=self.edit_user,
                on_delete=self.delete_user
            )
            self.user_table.setCellWidget(row, 5, actions_widget)

    def filter_users(self):
        """Applies search text and role filter to the user list."""
        search_text = self.search_input.text().lower()
        selected_role = self.filter_combo.currentText()
        
        filtered = []
        for user in self.all_users:
            matches_search = search_text in user.get('username', '').lower() or search_text in user.get('role', '').lower()
            matches_role = selected_role == "All Roles" or user.get('role') == selected_role
            
            if matches_search and matches_role:
                filtered.append(user)
                
        self.populate_table(filtered)

    def add_new_user(self):
        """Placeholder for opening the Add New User dialog."""
        show_success_message("Feature Stub", "Opening dialog to add a new user (API: users.create()).", self)
        # A real implementation would launch a UserDialog
        
    def edit_user(self, user_id: int):
        """Handles the 'Edit' action."""
        user = next((u for u in self.all_users if u['id'] == user_id), None)
        if not user: return
        
        # Mock API call for update: change status/role
        new_status = not user['is_active']
        new_data = {'is_active': new_status}
        
        # --- API Integration Point 5: users.update() ---
        resp = self.api.users.update(user_id, new_data)
        
        if resp.success:
            # Log action
            self.api.admin.log_desktop_action(
                user_id=self.current_user['id'],
                action="USER_UPDATED",
                target=user['username'],
                details={"status_change": new_status}
            )
            # Refresh UI
            show_success_message("Update Successful", f"User {user['username']} status toggled.", self)
            self.load_users()
        else:
            show_error_message("Update Failed", resp.error, self)
        
    def delete_user(self, user_id: int):
        """Handles the 'Delete' action."""
        user = next((u for u in self.all_users if u['id'] == user_id), None)
        if not user: return

        # In a real app, you would use a custom confirmation dialog here
        
        # --- API Integration Point 6: users.delete() ---
        resp = self.api.users.delete(user_id)
        
        if resp.success:
            # Log action
            self.api.admin.log_desktop_action(
                user_id=self.current_user['id'],
                action="USER_DELETED",
                target=user['username'],
                details={"user_id": user_id}
            )
            # Refresh UI
            show_success_message("Deletion Successful", f"User {user['username']} deleted.", self)
            self.load_users()
        else:
            show_error_message("Deletion Failed", resp.error, self)


class ActivityLogWidget(QWidget):
    """Displays a table of activity logs fetched from the Admin API endpoint."""
    def __init__(self, api_client: StockaDoodleAPI):
        super().__init__()
        self.api = api_client
        self.current_user = self.api.session.user_data
        self.all_logs: List[Dict[str, Any]] = []
        self.setup_ui()
        self.load_logs()

    def setup_ui(self):
        v_layout = QVBoxLayout(self)
        v_layout.setContentsMargins(0, 0, 0, 0)
        v_layout.setSpacing(10)
        
        # Header and Actions
        header_h_layout = QHBoxLayout()
        header_label = QLabel("Activity Logs")
        header_label.setObjectName("Header")
        header_h_layout.addWidget(header_label)

        header_h_layout.addStretch(1)
        
        # Filter by Source
        self.source_combo = QComboBox()
        self.source_combo.addItems(["All Sources", "Desktop App", "Postman"])
        self.source_combo.setFixedWidth(150)
        self.source_combo.currentIndexChanged.connect(self.filter_logs)
        header_h_layout.addWidget(self.source_combo)

        # Export Button (New Requirement)
        export_btn = QPushButton(get_feather_icon("download", "white", 16), "Export All")
        export_btn.setFixedWidth(120)
        export_btn.clicked.connect(self.export_logs)
        header_h_layout.addWidget(export_btn)

        v_layout.addLayout(header_h_layout)
        
        # Logs Table
        self.log_table = QTableWidget()
        self.log_table.setColumnCount(6)
        self.log_table.setHorizontalHeaderLabels(["ID", "Timestamp", "User", "Method", "Source", "Target/Details"])
        self.log_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.log_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.log_table.verticalHeader().setVisible(False)
        
        apply_table_styles(self.log_table)
        
        header = self.log_table.horizontalHeader()
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Stretch)
        self.log_table.setColumnWidth(0, 50)
        self.log_table.setColumnWidth(4, 120)
        
        v_layout.addWidget(self.log_table)

    def load_logs(self):
        """Fetches activity logs from the API and populates the table."""
        self.log_table.setRowCount(0)
        
        # --- API Integration Point 7: admin.get_activity_logs() ---
        resp = self.api.admin.get_activity_logs(limit=100)
        
        if resp.success:
            self.all_logs = resp.data
            self.populate_table(self.all_logs)
        else:
            self.all_logs = []
            show_error_message("Data Error", f"Failed to load activity logs: {resp.error}", self)

    def populate_table(self, logs: List[Dict[str, Any]]):
        """Fills the QTableWidget with log data."""
        self.log_table.setRowCount(len(logs))
        
        for row, log in enumerate(logs):
            # 0. ID
            item_id = QTableWidgetItem(str(log.get('id', 'N/A')))
            item_id.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.log_table.setItem(row, 0, item_id)
            
            # 1. Timestamp
            item_time = QTableWidgetItem(format_date(log.get('timestamp', 'N/A')))
            self.log_table.setItem(row, 1, item_time)
            
            # 2. User
            item_user = QTableWidgetItem(log.get('user_username', 'System'))
            self.log_table.setItem(row, 2, item_user)
            
            # 3. Method
            item_method = QTableWidgetItem(log.get('method', 'N/A'))
            self.log_table.setItem(row, 3, item_method)
            
            # 4. Source (BadgeLabel)
            source_badge = BadgeLabel(log.get('source', 'N/A'), log.get('source', ''))
            self.log_table.setCellWidget(row, 4, source_badge)
            
            # 5. Target/Details
            details = f"{log.get('target', 'N/A')}: {log.get('details', '')}"
            item_details = QTableWidgetItem(details)
            self.log_table.setItem(row, 5, item_details)

    def filter_logs(self):
        """Filters logs based on the selected source."""
        selected_source = self.source_combo.currentText()
        
        if selected_source == "All Sources":
            filtered = self.all_logs
        else:
            filtered = [log for log in self.all_logs if log.get('source') == selected_source]
            
        self.populate_table(filtered)

    def export_logs(self):
        """Placeholder for exporting logs to a file."""
        show_success_message("Export Complete", "Activity logs have been exported successfully to CSV/Excel (simulated).", self)


class AdminDashboardWidget(QWidget):
    """
    Main Admin Dashboard container, combining User Management and Activity Logs.
    This serves as the main page for the 'Dashboard' navigation item.
    """
    def __init__(self, api_client: StockaDoodleAPI):
        super().__init__()
        self.api = api_client
        
        self.user_management_widget = UserManagementWidget(api_client)
        self.activity_log_widget = ActivityLogWidget(api_client)

        self.setup_ui()

    def setup_ui(self):
        v_layout = QVBoxLayout(self)
        v_layout.setContentsMargins(20, 20, 20, 20)
        v_layout.setSpacing(20)

        # Main Dashboard Title
        title_label = QLabel("Admin Overview")
        title_label.setObjectName("Title")
        v_layout.addWidget(title_label)
        
        # KPI Cards (Placeholder for Admin Overview)
        kpi_frame = QFrame()
        kpi_frame.setLayout(QHBoxLayout())
        kpi_frame.layout().setSpacing(20)
        kpi_frame.layout().setContentsMargins(0, 0, 0, 0)
        
        kpi_frame.layout().addWidget(self._create_kpi_card("Total Users", str(len(MOCK_USERS)), "users"))
        kpi_frame.layout().addWidget(self._create_kpi_card("Active Products", "45", "package"))
        kpi_frame.layout().addWidget(self._create_kpi_card("Pending Sales", "3", "dollar-sign"))
        
        v_layout.addWidget(kpi_frame)

        # Content Split: User Management (60%) and Activity Log (40%)
        content_h_split = QHBoxLayout()
        content_h_split.setSpacing(20)

        # 1. User Management
        user_frame = QFrame()
        user_frame.setLayout(QVBoxLayout())
        user_frame.layout().setContentsMargins(0, 0, 0, 0)
        user_frame.layout().addWidget(self.user_management_widget)
        content_h_split.addWidget(user_frame, 3) # 60% weight

        # 2. Activity Log
        activity_frame = QFrame()
        activity_frame.setLayout(QVBoxLayout())
        activity_frame.layout().setContentsMargins(10, 10, 10, 10)
        activity_frame.layout().addWidget(self.activity_log_widget)
        
        activity_frame.setObjectName("Card")
        activity_frame.setStyleSheet(get_dashboard_card_style())
        
        content_h_split.addWidget(activity_frame, 2) # 40% weight

        v_layout.addLayout(content_h_split)
        v_layout.addStretch(1)

    def _create_kpi_card(self, title: str, value: str, icon_name: str) -> QFrame:
        """Helper to create a standard KPI card frame."""
        card = QFrame()
        card.setObjectName("Card")
        card.setStyleSheet(get_dashboard_card_style())
        
        v_layout = QVBoxLayout(card)
        v_layout.setSpacing(5)
        
        # Icon and Title
        h_header = QHBoxLayout()
        h_header.addWidget(QLabel(title))
        h_header.addStretch(1)
        icon_label = QLabel()
        icon_label.setPixmap(get_feather_icon(icon_name, AppConfig.PRIMARY_COLOR, 24).pixmap(QSize(24, 24)))
        h_header.addWidget(icon_label)
        v_layout.addLayout(h_header)
        
        # Value
        value_label = QLabel(value)
        value_label.setFont(QFont(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_TITLE, QFont.Weight.Black))
        value_label.setStyleSheet(f"color: {AppConfig.TEXT_DEFAULT};")
        v_layout.addWidget(value_label)
        
        return card