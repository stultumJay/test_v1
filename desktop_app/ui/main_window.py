from PyQt6.QtWidgets import (QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                             QPushButton, QLabel, QStackedWidget, QSizePolicy,
                             QMessageBox, QDialog)
from PyQt6.QtGui import QIcon, QFont, QPixmap
from PyQt6.QtCore import Qt, QSize
import os
from ui.dashboard_widgets import AdminDashboardWidget, ManagerDashboardWidget, RetailerDashboardWidget
from ui.product_management import ProductManagementWidget
from ui.user_management import UserManagementWidget
from ui.category_management import CategoryManagementWidget
from ui.sales_management import SalesManagementWidget
from utils.helpers import get_feather_icon
from utils.config import AppConfig
from utils.decorators import role_required
from core.activity_logger import ActivityLogger
from utils.styles import get_global_stylesheet  # Import global stylesheet


class MainWindow(QMainWindow):
    def __init__(self, current_user, parent=None):
        """
        Initialize the main window with user-specific content.
        The main window contains the sidebar navigation and content area.
        """
        super().__init__(parent)
        self.current_user = current_user
        self.logger = ActivityLogger()
        self.setWindowTitle("Inventory Management System")
        self.setMinimumSize(1024, 768)

        # Apply global stylesheet
        self.setStyleSheet(get_global_stylesheet())
        
        self.init_ui()

    def init_ui(self):
        """
        Initialize the user interface with widgets and layout.
        Creates the sidebar navigation and content area.
        """
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QHBoxLayout(central_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # --- Sidebar ---
        self.sidebar = QWidget()
        self.sidebar.setObjectName("sidebar")
        self.sidebar.setFixedWidth(220)
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(0, 0, 0, 0)
        sidebar_layout.setSpacing(0)
        sidebar_layout.setAlignment(Qt.AlignmentFlag.AlignTop)

        # App Logo
        logo_container = QWidget()
        logo_container.setObjectName("logoContainer")
        logo_container.setStyleSheet(f"""
            #logoContainer {{
                background-color: {AppConfig.DARK_BACKGROUND};
                padding: 15px 0px;
                border-bottom: 1px solid rgba(255,255,255,0.1);
            }}
        """)
        logo_layout = QHBoxLayout(logo_container)
        logo_layout.setContentsMargins(15, 5, 15, 5)
        
        logo_label = QLabel("IMS")
        logo_label.setStyleSheet(f"""
            font-size: 22px;
            font-weight: bold;
            color: {AppConfig.LIGHT_TEXT};
        """)
        version_label = QLabel("v1.0")
        version_label.setStyleSheet(f"color: rgba(255,255,255,0.5); font-size: 10px;")
        
        logo_layout.addWidget(logo_label)
        logo_layout.addWidget(version_label, alignment=Qt.AlignmentFlag.AlignBottom)
        sidebar_layout.addWidget(logo_container)

        # User Info
        user_info_widget = QWidget()
        user_info_widget.setObjectName("userInfoWidget")
        user_info_widget.setStyleSheet(f"""
            #userInfoWidget {{
                background-color: rgba(0,0,0,0.2);
                padding: 15px 0px;
                border-bottom: 1px solid rgba(255,255,255,0.05);
            }}
        """)
        user_info_layout = QVBoxLayout(user_info_widget)
        user_info_layout.setContentsMargins(15, 10, 15, 10)
        user_info_layout.setSpacing(5)

        # User avatar and info
        user_avatar_layout = QHBoxLayout()
        user_avatar_layout.setSpacing(10)
        
        user_icon_label = QLabel()
        user_icon_label.setPixmap(get_feather_icon("user", color="white", size=32).pixmap(32, 32))
        user_avatar_layout.addWidget(user_icon_label)
        
        user_details_layout = QVBoxLayout()
        user_details_layout.setSpacing(2)
        
        username_label = QLabel(self.current_user.get("username", "Guest"))
        username_label.setObjectName("userNameLabel")
        user_details_layout.addWidget(username_label)

        role_label = QLabel(self.current_user.get("role", "Unknown").capitalize())
        role_label.setStyleSheet(f"color: rgba(255,255,255,0.7); font-size: {AppConfig.FONT_SIZE_NORMAL-1}pt;")
        user_details_layout.addWidget(role_label)
        
        user_avatar_layout.addLayout(user_details_layout)
        user_info_layout.addLayout(user_avatar_layout)
        
        sidebar_layout.addWidget(user_info_widget)

        # Navigation label
        nav_label = QLabel("NAVIGATION")
        nav_label.setStyleSheet(f"""
            color: rgba(255,255,255,0.5);
            font-size: 10px;
            padding: 15px 15px 5px 15px;
            font-weight: bold;
        """)
        sidebar_layout.addWidget(nav_label)

        # Navigation Buttons
        self.btn_group = []  # To manage checked state for buttons

        self.dashboard_btn = self._create_nav_button("Dashboard", "home", "dashboard")
        self.product_btn = self._create_nav_button("Products", "package", "product_management")
        self.category_btn = self._create_nav_button("Categories", "grid", "category_management")
        self.user_btn = self._create_nav_button("Users", "users", "user_management")
        self.sales_btn = self._create_nav_button("Sales", "dollar-sign", "sales_management")

        sidebar_layout.addWidget(self.dashboard_btn)
        sidebar_layout.addWidget(self.product_btn)
        sidebar_layout.addWidget(self.category_btn)
        sidebar_layout.addWidget(self.user_btn)
        sidebar_layout.addWidget(self.sales_btn)

        sidebar_layout.addStretch()  # Pushes buttons to top

        # Logout Button
        logout_btn = QPushButton("Logout")
        logout_btn.setIcon(get_feather_icon("log-out", size=16))
        logout_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: rgba(231, 76, 60, 0.8);
                color: white;
                border: none;
                padding: 10px;
                margin: 15px;
                border-radius: 5px;
                text-align: center;
            }}
            QPushButton:hover {{
                background-color: rgba(231, 76, 60, 1.0);
            }}
        """)
        logout_btn.clicked.connect(self.logout)
        sidebar_layout.addWidget(logout_btn)

        main_layout.addWidget(self.sidebar)

        # --- Content Area ---
        content_container = QWidget()
        content_container.setObjectName("contentArea")
        content_layout = QVBoxLayout(content_container)
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)

        self.content_area = QStackedWidget()
        content_layout.addWidget(self.content_area)
        main_layout.addWidget(content_container, 1)  # 1 = stretch factor

        # Load all pages
        self._load_pages()
        
        # Apply role-based permissions
        self._apply_role_permissions()
        
        # Set initial page
        self._set_initial_page()

    def _create_nav_button(self, text, icon_name, page_name):
        button = QPushButton(text)
        button.setIcon(get_feather_icon(icon_name, size=20))
        button.setCheckable(True)
        button.clicked.connect(lambda: self._switch_page(page_name, button))
        self.btn_group.append(button)
        return button

    def _switch_page(self, page_name, clicked_button):
        # Uncheck all buttons except the clicked one
        for btn in self.btn_group:
            if btn != clicked_button:
                btn.setChecked(False)
        clicked_button.setChecked(True)

        # Find the widget by object name (which is set to page_name)
        for i in range(self.content_area.count()):
            widget = self.content_area.widget(i)
            if widget.objectName() == page_name:
                # Store current page to avoid refreshing if we're already on it
                current_widget = self.content_area.currentWidget()
                if current_widget != widget:
                    # Only switch and refresh if we're actually changing pages
                    self.content_area.setCurrentWidget(widget)
                    
                    # Refresh data in the new widget - but only call specific methods if they exist
                    # Use hasattr check to avoid errors and prevent multiple pop-ups
                    if hasattr(widget, 'load_dashboard_data') and page_name == "dashboard":
                        # Call dashboard data loading only if method exists and we're going to dashboard
                        widget.load_dashboard_data()
                    elif hasattr(widget, 'refresh_products_display') and page_name == "product_management":
                        # Only refresh product display if method exists and we're going to product management
                        widget.refresh_products_display()
                    elif hasattr(widget, 'load_users') and page_name == "user_management":
                        widget.load_users()
                    elif hasattr(widget, 'load_categories') and page_name == "category_management":
                        widget.load_categories()
                    elif hasattr(widget, 'load_sales_data') and page_name == "sales_management":
                        widget.load_sales_data()
                break

    def _load_pages(self):
        # Dashboard (role-specific)
        if self.current_user['role'] == 'admin':
            dashboard_widget = AdminDashboardWidget(self.current_user)
        elif self.current_user['role'] == 'manager':
            dashboard_widget = ManagerDashboardWidget(self.current_user)
        else:  # retailer
            dashboard_widget = RetailerDashboardWidget(self.current_user)
        dashboard_widget.setObjectName("dashboard")
        self.content_area.addWidget(dashboard_widget)

        # Other pages
        product_widget = ProductManagementWidget(self.current_user)
        product_widget.setObjectName("product_management")
        self.content_area.addWidget(product_widget)

        category_widget = CategoryManagementWidget(self.current_user)
        category_widget.setObjectName("category_management")
        self.content_area.addWidget(category_widget)

        user_widget = UserManagementWidget(self.current_user)
        user_widget.setObjectName("user_management")
        self.content_area.addWidget(user_widget)

        sales_widget = SalesManagementWidget(self.current_user)
        sales_widget.setObjectName("sales_management")
        self.content_area.addWidget(sales_widget)

    def _set_initial_page(self):
        # Set dashboard as initial page and mark its button as checked
        self.content_area.setCurrentIndex(0)  # Dashboard is always the first added
        self.dashboard_btn.setChecked(True)

    def _apply_role_permissions(self):
        role = self.current_user['role']
        if role == 'retailer':
            self.user_btn.hide()
            self.category_btn.hide()
            # Sales management might be restricted to just viewing own sales, not full reports
            # For now, sales_management is visible to retailer, but its internal logic might restrict
            # what they can do (e.g., only record sales, not view all reports).
            # The AdminDashboardWidget and ManagerDashboardWidget are loaded based on role,
            # and their internal buttons (like Add Stock/Edit Product) are also role-restricted.
        elif role == 'manager':
            self.user_btn.hide()  # Managers might not manage users
            # Other pages visible by default
        elif role == 'admin':
            # Ensure admin has access to all sections
            self.product_btn.show()  # Explicitly show product management for admin
            self.category_btn.show()
            self.user_btn.show()
            self.sales_btn.show()
        # Admin has access to all by default

    def logout(self):
        reply = QMessageBox.question(self, "Logout", "Are you sure you want to logout?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            # Close the main window
            self.hide()
            
            # Show login window
            from ui.login_window import LoginWindow
            self.login_window = LoginWindow()
            self.login_window.show()
            
            # Set up a connection for when login is successful
            if hasattr(self.login_window, 'accepted'):
                self.login_window.accepted.connect(self.close)  # Close main window when login accepts
            
            # Alternatively, you can connect to the finished signal with a lambda to check result
            self.login_window.finished.connect(
                lambda result: self.close() if result == QDialog.DialogCode.Accepted else self.show()
            )