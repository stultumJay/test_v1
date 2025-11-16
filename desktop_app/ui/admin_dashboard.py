import sys
from PyQt6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QTableWidget, QTableWidgetItem, QPushButton, QLineEdit,
    QComboBox, QFrame, QSizePolicy, QHeaderView, QToolButton, QSpacerItem
)
from PyQt6.QtGui import QFont, QIcon, QAction
from PyQt6.QtCore import Qt, QSize, QRect

# --- Minimal Configuration and Utility for Demo ---
# In a full application, these would be imported from utils/config.py
class AppConfig:
    FONT_FAMILY = "Inter"
    FONT_SIZE_TITLE = 18
    FONT_SIZE_NORMAL = 10
    PRIMARY_BLUE = "#3a7afb"
    SECONDARY_DARK = "#2c3e50"
    BORDER_GRAY = "#bdc3c7"
    BACKGROUND_LIGHT = "#f5f7fa"
    TEXT_DEFAULT = "#34495e"

def get_feather_icon(name):
    # Minimal icon mapping using Unicode characters for demonstration
    icons = {
        "download": "⭳", "plus": "+", "search": "🔎",
        "edit": "✎", "key": "🔑", "trash": "🗑️"
    }
    return icons.get(name, "?")

# --- Custom Table Cell Widgets ---

class BadgeLabel(QLabel):
    """A custom QLabel for displaying role or status as a colored badge."""
    def __init__(self, text, badge_type):
        super().__init__(text)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedWidth(80) # Fixed width for uniform badges
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        styles = {
            "Admin": ("#e6e6ff", AppConfig.PRIMARY_BLUE), # Light Lavender background, Primary Blue text
            "Manager": ("#e0f7fa", "#00bcd4"), # Light Cyan background, Cyan text
            "Retailer": ("#e8f5e9", "#4caf50"), # Light Green background, Green text
            "Active": ("#e8f5e9", "#4caf50"), # Light Green background, Green text
            "Suspended": ("#fff8e1", "#ffc107"), # Light Yellow background, Gold text
            "Inactive": ("#ffebee", "#f44336"), # Light Red background, Red text
        }
        
        bg_color, text_color = styles.get(badge_type, ("#f0f0f0", AppConfig.TEXT_DEFAULT))

        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg_color};
                color: {text_color};
                border-radius: 8px;
                padding: 4px 8px;
                font-weight: bold;
                font-size: {AppConfig.FONT_SIZE_NORMAL - 1}pt;
            }}
        """)

class NameCellWidget(QWidget):
    """Custom widget for the 'Name' column (Avatar + Name/Department)."""
    def __init__(self, initials, name, department, role_color):
        super().__init__()
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 5, 0, 5)
        self.main_layout.setSpacing(10)

        # 1. Avatar Label
        self.avatar = QLabel(initials)
        self.avatar.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.avatar.setFixedSize(QSize(32, 32))
        self.avatar.setStyleSheet(f"""
            QLabel {{
                background-color: {role_color};
                color: white;
                border-radius: 16px; /* Makes it circular */
                font-size: {AppConfig.FONT_SIZE_NORMAL}pt;
                font-weight: bold;
            }}
        """)

        # 2. Text (Name and Department)
        self.text_container = QWidget()
        self.text_layout = QVBoxLayout(self.text_container)
        self.text_layout.setContentsMargins(0, 0, 0, 0)
        self.text_layout.setSpacing(0)

        self.name_label = QLabel(name)
        self.name_label.setFont(QFont(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_NORMAL + 1, QFont.Weight.Bold))
        self.name_label.setStyleSheet(f"color: {AppConfig.TEXT_DEFAULT};")

        self.dept_label = QLabel(department)
        self.dept_label.setFont(QFont(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_NORMAL - 1))
        self.dept_label.setStyleSheet("color: #7f8c8d;") # Gray color for department

        self.text_layout.addWidget(self.name_label)
        self.text_layout.addWidget(self.dept_label)

        self.main_layout.addWidget(self.avatar)
        self.main_layout.addWidget(self.text_container)
        self.main_layout.addStretch()

class ActionButtonsWidget(QWidget):
    """Custom widget for the 'Actions' column (Edit, Perms, Delete buttons)."""
    def __init__(self):
        super().__init__()
        self.main_layout = QHBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(5)
        self.main_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self.edit_btn = self._create_tool_button("edit", "#3498db")
        self.perms_btn = self._create_tool_button("key", "#f39c12")
        self.delete_btn = self._create_tool_button("trash", "#e74c3c")

        self.main_layout.addWidget(self.edit_btn)
        self.main_layout.addWidget(self.perms_btn)
        self.main_layout.addWidget(self.delete_btn)

    def _create_tool_button(self, icon_name, color):
        btn = QToolButton()
        btn.setText(get_feather_icon(icon_name))
        btn.setIconSize(QSize(18, 18))
        btn.setFixedSize(QSize(30, 30))
        btn.setStyleSheet(f"""
            QToolButton {{
                border: 1px solid {AppConfig.BORDER_GRAY};
                border-radius: 8px;
                background-color: white;
                color: {color};
                font-size: 10pt;
            }}
            QToolButton:hover {{
                background-color: {AppConfig.BACKGROUND_LIGHT};
            }}
        """)
        return btn

# --- Main Administration Widget ---

class AdminUserManagementWidget(QWidget):
    """The main content widget for the Administration/User Management screen."""
    
    # Mock data for demonstration
    USER_DATA = [
        {"initials": "DT", "name": "David Thompson", "dept": "Sales", "role": "Retailer", "email": "david.t@example.com", "last_login": "2025-11-15", "status": "Active", "color": "#2ecc71"},
        {"initials": "SM", "name": "Sarah Miller", "dept": "IT", "role": "Admin", "email": "sarah.m@example.com", "last_login": "2025-11-14", "status": "Suspended", "color": AppConfig.PRIMARY_BLUE},
        {"initials": "JL", "name": "John Lewis", "dept": "HR", "role": "Manager", "email": "john.l@example.com", "last_login": "2025-11-01", "status": "Active", "color": "#9b59b6"},
        {"initials": "EA", "name": "Emily Adams", "dept": "Marketing", "role": "Retailer", "email": "emily.a@example.com", "last_login": "2025-10-28", "status": "Inactive", "color": "#f1c40f"},
        {"initials": "MB", "name": "Michael Brown", "dept": "Finance", "role": "Manager", "email": "michael.b@example.com", "last_login": "2025-11-16", "status": "Active", "color": "#1abc9c"},
        {"initials": "NW", "name": "Nina White", "dept": "Warehouse", "role": "Retailer", "email": "nina.w@example.com", "last_login": "2025-11-15", "status": "Active", "color": "#34495e"},
    ]
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("AdminUserManagementWidget")
        self.setStyleSheet(f"#{self.objectName()} {{ background-color: white; }}")
        
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(30, 30, 30, 30)
        self.main_layout.setSpacing(20)

        self._setup_header()
        self._setup_search_and_filters()
        self._setup_user_table()
        
        # Load mock data
        self.load_user_data()

    def _setup_header(self):
        """Sets up the title and action buttons area."""
        header_frame = QFrame()
        header_layout = QHBoxLayout(header_frame)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(10)

        # Title and Description
        title_container = QWidget()
        title_vbox = QVBoxLayout(title_container)
        title_vbox.setContentsMargins(0, 0, 0, 0)
        title_vbox.setSpacing(0)

        title_label = QLabel("User Management")
        title_label.setFont(QFont(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_TITLE, QFont.Weight.Bold))
        title_label.setStyleSheet(f"color: {AppConfig.SECONDARY_DARK};")
        
        desc_label = QLabel("Manage user accounts, roles, and permissions.")
        desc_label.setFont(QFont(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_NORMAL))
        desc_label.setStyleSheet("color: #7f8c8d;")

        title_vbox.addWidget(title_label)
        title_vbox.addWidget(desc_label)

        # Action Buttons
        export_btn = self._create_action_button("Export All", "download", is_primary=False)
        add_user_btn = self._create_action_button("Add User", "plus", is_primary=True)
        
        header_layout.addWidget(title_container)
        header_layout.addStretch()
        header_layout.addWidget(export_btn)
        header_layout.addWidget(add_user_btn)
        
        self.main_layout.addWidget(header_frame)

    def _create_action_button(self, text, icon_name, is_primary):
        """Helper to create styled action buttons."""
        button = QPushButton(f"  {get_feather_icon(icon_name)} {text}")
        button.setFixedSize(QSize(150, 38))
        font = QFont(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_NORMAL, QFont.Weight.Bold)
        button.setFont(font)

        if is_primary:
            style = f"""
                QPushButton {{
                    background-color: {AppConfig.PRIMARY_BLUE};
                    color: white;
                    border: none;
                    border-radius: 8px;
                    padding: 8px 15px;
                }}
                QPushButton:hover {{
                    background-color: #3168d1;
                }}
            """
        else:
            style = f"""
                QPushButton {{
                    background-color: {AppConfig.BACKGROUND_LIGHT};
                    color: {AppConfig.TEXT_DEFAULT};
                    border: 1px solid {AppConfig.BORDER_GRAY};
                    border-radius: 8px;
                    padding: 8px 15px;
                }}
                QPushButton:hover {{
                    background-color: #dfe4e8;
                }}
            """
        button.setStyleSheet(style)
        return button

    def _setup_search_and_filters(self):
        """Sets up the search bar and filter dropdowns."""
        filter_container = QFrame()
        filter_vbox = QVBoxLayout(filter_container)
        filter_vbox.setContentsMargins(0, 0, 0, 0)
        filter_vbox.setSpacing(15)

        # 1. Search Bar
        search_line = QLineEdit()
        search_line.setPlaceholderText("Search users by name, email, or department...")
        search_line.setFixedHeight(38)
        search_line.setFont(QFont(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_NORMAL))
        
        # Add a magnifying glass icon/text as a prefix to the search bar
        search_line.setTextMargins(30, 0, 10, 0)
        
        search_icon_label = QLabel(get_feather_icon("search"))
        search_icon_label.setStyleSheet(f"""
            QLabel {{
                padding-left: 10px;
                font-size: 10pt;
                color: #7f8c8d;
            }}
        """)
        search_icon_label.setFixedSize(QSize(30, 38))
        
        # Use QAction or an overlaid widget for the icon (using QAction for simplicity)
        search_action = QAction(search_line)
        search_action.setText(get_feather_icon("search"))
        search_line.addAction(search_action, QLineEdit.ActionPosition.LeadingPosition)

        search_line.setStyleSheet(f"""
            QLineEdit {{
                border: 1px solid {AppConfig.BORDER_GRAY};
                border-radius: 8px;
                padding-left: 10px;
                background-color: white;
            }}
            QLineEdit:focus {{
                border: 1px solid {AppConfig.PRIMARY_BLUE};
            }}
        """)
        
        filter_vbox.addWidget(search_line)

        # 2. Filters Row
        filter_hbox = QHBoxLayout()
        filter_hbox.setContentsMargins(0, 0, 0, 0)
        filter_hbox.setSpacing(20)

        # Helper function for creating a filter group
        def create_filter_group(label_text, options):
            group_widget = QWidget()
            group_vbox = QVBoxLayout(group_widget)
            group_vbox.setContentsMargins(0, 0, 0, 0)
            group_vbox.setSpacing(5)

            label = QLabel(label_text)
            label.setStyleSheet(f"color: {AppConfig.TEXT_DEFAULT}; font-weight: bold; font-size: {AppConfig.FONT_SIZE_NORMAL - 1}pt;")

            combo = QComboBox()
            combo.addItems(options)
            combo.setFixedWidth(150)
            combo.setFixedHeight(34)
            combo.setFont(QFont(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_NORMAL))
            combo.setStyleSheet(f"""
                QComboBox {{
                    border: 1px solid {AppConfig.BORDER_GRAY};
                    border-radius: 6px;
                    padding: 5px 10px;
                    background-color: white;
                }}
                QComboBox::drop-down {{
                    border: none;
                    width: 20px;
                }}
            """)
            
            group_vbox.addWidget(label)
            group_vbox.addWidget(combo)
            return group_widget

        filter_hbox.addWidget(create_filter_group("Filter by Role", ["All Roles", "Admin", "Manager", "Retailer"]))
        filter_hbox.addWidget(create_filter_group("Filter by Status", ["All Statuses", "Active", "Suspended", "Inactive"]))
        filter_hbox.addWidget(create_filter_group("Filter by Department", ["All Depts", "Sales", "IT", "HR", "Marketing", "Finance", "Warehouse"]))
        
        # Status Label on the right
        status_label = QLabel(f"Showing {len(self.USER_DATA)} of {len(self.USER_DATA)} users")
        status_label.setStyleSheet("color: #7f8c8d; font-size: 10pt;")
        
        filter_hbox.addStretch()
        filter_hbox.addWidget(status_label)

        filter_vbox.addLayout(filter_hbox)
        self.main_layout.addWidget(filter_container)

    def _setup_user_table(self):
        """Sets up the QTableWidget for user data."""
        self.table_widget = QTableWidget()
        self.table_widget.setColumnCount(6)
        self.table_widget.setHorizontalHeaderLabels(["Name", "Role", "Email", "Last Login", "Status", "Actions"])
        self.table_widget.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table_widget.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table_widget.setShowGrid(False)
        self.table_widget.verticalHeader().setVisible(False)
        self.table_widget.horizontalHeader().setStretchLastSection(False)
        
        # Styling the header
        header_font = QFont(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_NORMAL, QFont.Weight.Bold)
        self.table_widget.horizontalHeader().setFont(header_font)
        
        self.table_widget.setStyleSheet(f"""
            QTableWidget {{
                border: 1px solid {AppConfig.BORDER_GRAY};
                border-radius: 12px;
                background-color: white;
                font-size: {AppConfig.FONT_SIZE_NORMAL}pt;
            }}
            QHeaderView::section {{
                background-color: {AppConfig.BACKGROUND_LIGHT};
                color: {AppConfig.TEXT_DEFAULT};
                padding: 10px 5px;
                border: none;
                border-bottom: 1px solid {AppConfig.BORDER_GRAY};
            }}
            QHeaderView::section:last {{
                border-right: none;
            }}
            QTableWidget::item {{
                padding-left: 5px;
            }}
        """)
        
        # Set column widths (approximate distribution)
        header = self.table_widget.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch) # Name
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed) # Role
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch) # Email
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Fixed) # Last Login
        header.setSectionResizeMode(4, QHeaderView.ResizeMode.Fixed) # Status
        header.setSectionResizeMode(5, QHeaderView.ResizeMode.Fixed) # Actions

        self.table_widget.setColumnWidth(1, 100)
        self.table_widget.setColumnWidth(3, 120)
        self.table_widget.setColumnWidth(4, 100)
        self.table_widget.setColumnWidth(5, 120)

        self.main_layout.addWidget(self.table_widget)

    def load_user_data(self):
        """Populates the QTableWidget with mock user data."""
        self.table_widget.setRowCount(len(self.USER_DATA))
        self.table_widget.verticalHeader().setDefaultSectionSize(55) # Taller rows for custom widgets

        for row, data in enumerate(self.USER_DATA):
            # 0. Name/Dept (Custom Widget)
            name_widget = NameCellWidget(
                data["initials"],
                data["name"],
                data["dept"],
                data["color"]
            )
            self.table_widget.setCellWidget(row, 0, name_widget)

            # 1. Role (Custom Badge)
            role_badge = BadgeLabel(data["role"], data["role"])
            self.table_widget.setCellWidget(row, 1, role_badge)

            # 2. Email (Simple Text)
            email_item = QTableWidgetItem(data["email"])
            self.table_widget.setItem(row, 2, email_item)

            # 3. Last Login (Simple Text)
            login_item = QTableWidgetItem(data["last_login"])
            login_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.table_widget.setItem(row, 3, login_item)

            # 4. Status (Custom Badge)
            status_badge = BadgeLabel(data["status"], data["status"])
            self.table_widget.setCellWidget(row, 4, status_badge)

            # 5. Actions (Custom Buttons)
            actions_widget = ActionButtonsWidget()
            self.table_widget.setCellWidget(row, 5, actions_widget)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Create a wrapper window to hold the Admin widget and mimic the full app look
    main_window = QWidget()
    main_window.setWindowTitle("Administration - User Management")
    main_window.setGeometry(100, 100, 1000, 700)
    
    # Add a simple sidebar placeholder for context
    h_layout = QHBoxLayout(main_window)
    h_layout.setContentsMargins(0, 0, 0, 0)
    h_layout.setSpacing(0)
    
    sidebar = QFrame()
    sidebar.setFixedWidth(220)
    sidebar.setStyleSheet("background-color: #2c3e50; border-right: 1px solid #34495e;")
    sidebar_layout = QVBoxLayout(sidebar)
    sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)
    
    # The actual 'Administration' tab entry
    admin_label = QLabel("  Administration")
    admin_label.setStyleSheet("color: white; padding: 10px; margin-top: 50px; background-color: #34495e; border-left: 5px solid #3a7afb; font-weight: bold;")
    sidebar_layout.addWidget(admin_label)
    
    h_layout.addWidget(sidebar)
    
    # Add the main content widget
    admin_widget = AdminUserManagementWidget()
    h_layout.addWidget(admin_widget)

    main_window.show()
    sys.exit(app.exec())