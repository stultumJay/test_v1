"""
Admin Dashboard Widget - System Overview
High-level metrics, user activity, and quick actions
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QTableWidget, QTableWidgetItem, QFrame, QGridLayout, QHeaderView
    
)
from desktop_app.ui.user_profile import UserProfileTab
from PyQt6.QtCore import Qt, QTimer, QSize
from PyQt6.QtGui import QFont
from datetime import datetime

from api_client.stockadoodle_api import StockaDoodleAPI
from utils.config import AppConfig
from utils.decorators import role_required
from utils.helpers import get_feather_icon
from utils.styles import get_dashboard_card_style, apply_table_styles


class KPICard(QFrame):
    """Reusable KPI Card Widget"""
    def __init__(self, title: str, icon_name: str, color: str, parent=None):
        super().__init__(parent)
        self.title = title
        self.color = color
        
        self.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {color}22, stop:1 {color}44);
                border: 1px solid {color}44;
                border-radius: 12px;
                padding: 20px;
                min-height: 120px;
            }}
        """)
        
        layout = QVBoxLayout(self)
        layout.setSpacing(10)
        
        # Icon and Title Row
        header = QHBoxLayout()
        
        icon_label = QLabel()
        icon_label.setPixmap(get_feather_icon(icon_name, "white", 24).pixmap(QSize(24, 24)))
        header.addWidget(icon_label)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #ccc; font-size: 11pt;")
        header.addWidget(title_label)
        header.addStretch()
        
        layout.addLayout(header)
        
        # Value Label
        self.value_label = QLabel("0")
        self.value_label.setStyleSheet(f"color: white; font-size: 28pt; font-weight: bold;")
        self.value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.value_label)
        
    def set_value(self, value):
        """Update the displayed value"""
        self.value_label.setText(str(value))


class AdminDashboardWidget(QWidget):
    """Main Admin Dashboard - System Overview"""
    
    def __init__(self, api_client: StockaDoodleAPI, parent=None):
        super().__init__(parent)
        self.api = api_client
        
        self.setStyleSheet(f"background-color: {AppConfig.BACKGROUND_COLOR};")
        self.user_data = user_data
        self.setWindowTitle(f"Stockadoodle - Admin Dashboard ({user_data['username']})")
        self.init_ui()
        
        # Load data asynchronously
        QTimer.singleShot(100, self.load_dashboard_data)
        
    def init_ui(self):
        """Initialize the UI layout"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(20)
        
        # Welcome Header
        header = self._create_welcome_header()
        main_layout.addWidget(header)
        
        # KPI Cards Row
        kpi_layout = self._create_kpi_section()
        main_layout.addLayout(kpi_layout)
        
        # Content Split: Activity (60%) + Quick Actions (40%)
        content_layout = QHBoxLayout()
        content_layout.setSpacing(20)
        
        # Left: Recent Activity
        activity_section = self._create_activity_section()
        content_layout.addWidget(activity_section, 60)
        
        # Right: Quick Actions
        actions_section = self._create_quick_actions()
        content_layout.addWidget(actions_section, 40)
        
        main_layout.addLayout(content_layout)
        main_layout.addStretch()
        
    def _create_welcome_header(self) -> QFrame:
        """Create the welcome banner"""
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {AppConfig.PRIMARY_COLOR}, stop:1 {AppConfig.SECONDARY_COLOR});
                border-radius: 12px;
                padding: 20px;
            }}
        """)
        
        layout = QVBoxLayout(header)
        
        welcome_label = QLabel("Welcome, Admin")
        welcome_label.setFont(QFont(AppConfig.FONT_FAMILY, 24, QFont.Weight.Bold))
        welcome_label.setStyleSheet("color: white;")
        layout.addWidget(welcome_label)
        
        date_label = QLabel(datetime.now().strftime("%A, %B %d, %Y"))
        date_label.setStyleSheet("color: rgba(255,255,255,0.8); font-size: 12pt;")
        layout.addWidget(date_label)
        
        return header
        
    def _create_kpi_section(self) -> QHBoxLayout:
        """Create KPI cards row"""
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(20)
        
        # Total Products Card
        self.products_card = KPICard("Total Products", "package", "#00B894")
        kpi_layout.addWidget(self.products_card)
        
        # Total Users Card
        self.users_card = KPICard("Total Users", "users", "#6C5CE7")
        kpi_layout.addWidget(self.users_card)
        
        # Total Sales Card
        self.sales_card = KPICard("Total Sales", "dollar-sign", "#D63031")
        kpi_layout.addWidget(self.sales_card)
        
        return kpi_layout
        
    def _create_activity_section(self) -> QFrame:
        """Create recent activity log section"""
        section = QFrame()
        section.setStyleSheet(f"""
            QFrame {{
                background-color: {AppConfig.CARD_BACKGROUND};
                border-radius: 12px;
                padding: 20px;
            }}
        """)
        
        layout = QVBoxLayout(section)
        
        # Section Title
        title = QLabel("Recent User Activity")
        title.setFont(QFont(AppConfig.FONT_FAMILY, 16, QFont.Weight.Bold))
        title.setStyleSheet("color: white; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Activity Table
        self.activity_table = QTableWidget(0, 4)
        self.activity_table.setHorizontalHeaderLabels(["User", "Action", "Target", "Time"])
        apply_table_styles(self.activity_table)
        
        # Configure columns
        header = self.activity_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        
        self.activity_table.setMinimumHeight(400)
        layout.addWidget(self.activity_table)
        
        return section
        
    def _create_quick_actions(self) -> QFrame:
        """Create quick action buttons section"""
        section = QFrame()
        section.setStyleSheet(f"""
            QFrame {{
                background-color: {AppConfig.CARD_BACKGROUND};
                border-radius: 12px;
                padding: 20px;
            }}
        """)
        
        layout = QVBoxLayout(section)
        
        # Section Title
        title = QLabel("Quick Actions")
        title.setFont(QFont(AppConfig.FONT_FAMILY, 16, QFont.Weight.Bold))
        title.setStyleSheet("color: white; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Action Buttons Grid
        grid = QGridLayout()
        grid.setSpacing(15)
        
        # Manage Users Button
        users_btn = self._create_action_button(
            "Manage Users", "users", AppConfig.PRIMARY_COLOR
        )
        grid.addWidget(users_btn, 0, 0)
        
        # View Products Button
        products_btn = self._create_action_button(
            "View Products", "package", AppConfig.SECONDARY_COLOR
        )
        grid.addWidget(products_btn, 0, 1)
        
        # System Settings Button
        settings_btn = self._create_action_button(
            "System Settings", "settings", "#74B9FF"
        )
        grid.addWidget(settings_btn, 1, 0)
        
        # Audit Trail Button
        audit_btn = self._create_action_button(
            "View Audit Trail", "file-text", "#FDCB6E"
        )
        grid.addWidget(audit_btn, 1, 1)
        
        layout.addLayout(grid)
        layout.addStretch()
        
        return section
        
    def _create_action_button(self, text: str, icon: str, color: str) -> QPushButton:
        """Create a styled action button"""
        btn = QPushButton(text)
        btn.setIcon(get_feather_icon(icon, "white", 20))
        btn.setIconSize(QSize(20, 20))
        btn.setMinimumHeight(80)
        btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {color};
                color: white;
                border: none;
                border-radius: 8px;
                padding: 15px;
                font-size: 12pt;
                font-weight: bold;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {color}dd;
            }}
        """)
        return btn
        
    @role_required('Admin')
    def load_dashboard_data(self):
        """Load dashboard data from API"""
        try:
            # Fetch admin dashboard metrics
            resp = self.api.dashboard.admin()
            
            if resp.success:
                data = resp.data
                self.products_card.set_value(data.get('total_products', 0))
                self.users_card.set_value(data.get('total_users', 0))
                self.sales_card.set_value(data.get('total_sales', 0))
            
            # Fetch recent activity logs
            logs_resp = self.api.logs.desktop.get_recent(limit=10)
            
            if logs_resp.success:
                self._populate_activity_table(logs_resp.data)
                
        except Exception as e:
            print(f"Error loading dashboard data: {e}")
            
    def _populate_activity_table(self, logs: list):
        """Populate the activity table with log data"""
        self.activity_table.setRowCount(0)
        
        for log in logs:
            row = self.activity_table.rowCount()
            self.activity_table.insertRow(row)
            
            # User
            user = log.get('username', 'System')
            self.activity_table.setItem(row, 0, QTableWidgetItem(user))
            
            # Action
            action = log.get('action', 'N/A')
            self.activity_table.setItem(row, 1, QTableWidgetItem(action))
            
            # Target
            target = log.get('target', 'N/A')
            self.activity_table.setItem(row, 2, QTableWidgetItem(target))
            
            # Time
            timestamp = log.get('timestamp', '')
            if timestamp:
                # Format timestamp nicely
                try:
                    dt = datetime.fromisoformat(timestamp)
                    time_str = dt.strftime("%I:%M %p")
                except:
                    time_str = timestamp[:10]
            else:
                time_str = 'N/A'
            self.activity_table.setItem(row, 3, QTableWidgetItem(time_str))