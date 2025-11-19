from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget, 
    QPushButton, QLabel, QFrame, QSizePolicy, QSpacerItem, QToolButton
)
from PyQt6.QtGui import QIcon, QFont, QPixmap
from PyQt6.QtCore import Qt, QSize

# Import UI components (stubs are fine for now)
from ui.admin_dashboard import AdminDashboardWidget
# from ui.manager_dashboard import ManagerDashboardWidget # Phase 2
# from ui.retailer_pos import RetailerDashboardWidget # Phase 2
# from ui.product_management import ProductManagementWidget # Phase 2
# from ui.category_management import CategoryManagementWidget # Phase 3
# from ui.sales_management import SalesManagementWidget # Phase 3

from api_client.stockadoodle_api import StockaDoodleAPI
from utils.config import AppConfig, SESSION
from utils.styles import get_global_stylesheet, get_dashboard_card_style
from utils.helpers import get_feather_icon

class MainWindow(QMainWindow):
    """
    Main application window with unified dark sidebar, top bar, and stacked widget
    for role-based navigation.
    """
    def __init__(self, api_client: StockaDoodleAPI):
        super().__init__()
        self.api = api_client
        self.session = SESSION
        self.current_user = self.session.user_data
        
        self.setWindowTitle("StockaDoodle Inventory")
        self.setMinimumSize(1200, 800)
        self.setStyleSheet(get_global_stylesheet())
        
        self.current_role = self.session.get_role()
        
        self.setup_ui()
        self.show_default_page()
        
    def setup_ui(self):
        """Initializes the main layout: Sidebar, Top Bar, and Content Area."""
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        
        main_h_layout = QHBoxLayout(central_widget)
        main_h_layout.setContentsMargins(0, 0, 0, 0)
        main_h_layout.setSpacing(0)
        
        # 1. Unified Dark Sidebar
        self.sidebar = self._create_sidebar()
        main_h_layout.addWidget(self.sidebar)
        
        # Content container (Top Bar + Stacked Widget)
        content_v_container = QWidget()
        content_v_layout = QVBoxLayout(content_v_container)
        content_v_layout.setContentsMargins(0, 0, 0, 0)
        content_v_layout.setSpacing(0)
        
        # 2. Top Bar
        self.top_bar = self._create_top_bar()
        content_v_layout.addWidget(self.top_bar)
        
        # 3. QStackedWidget for dashboard pages
        self.stacked_widget = QStackedWidget()
        self._initialize_dashboards()
        content_v_layout.addWidget(self.stacked_widget)
        
        main_h_layout.addWidget(content_v_container)

    def _create_sidebar(self) -> QWidget:
        """Creates the dark navigation sidebar (220px width)."""
        sidebar = QWidget()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(220)
        
        v_layout = QVBoxLayout(sidebar)
        v_layout.setContentsMargins(10, 20, 10, 10)
        v_layout.setSpacing(10)
        
        # Sidebar Logo/Title
        logo_label = QLabel("StockaDoodle")
        logo_label.setObjectName("Title")
        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        logo_label.setStyleSheet(f"color: white; margin-bottom: 20px; font-size: {AppConfig.FONT_SIZE_TITLE}pt;")
        v_layout.addWidget(logo_label)
        
        # Navigation Buttons (Role-based visibility)
        self.nav_buttons: Dict[str, QPushButton] = {}
        nav_items = [
            ("Dashboard", "activity", ["Admin", "Manager", "Retailer"]),
            ("User Management", "users", ["Admin"]),
            ("Product Management", "package", ["Admin", "Manager"]),
            ("Category Management", "settings", ["Admin", "Manager"]),
            ("Sales Management", "dollar-sign", ["Admin", "Manager"]),
            ("Retailer POS", "shopping-cart", ["Retailer"]),
        ]
        
        for name, icon_name, roles in nav_items:
            if self.current_role in roles:
                button = QPushButton(name)
                button.setObjectName(name.replace(" ", ""))
                button.setProperty("class", "SidebarButton")
                button.setIcon(get_feather_icon(icon_name, AppConfig.TEXT_MUTED))
                button.setIconSize(QSize(20, 20))
                button.setCheckable(True)
                button.clicked.connect(lambda _, n=name: self.switch_page(n))
                v_layout.addWidget(button)
                self.nav_buttons[name] = button

        v_layout.addStretch(1)
        
        return sidebar

    def _create_top_bar(self) -> QWidget:
        """Creates the top bar with user info and logout."""
        top_bar = QFrame()
        top_bar.setFixedHeight(60)
        top_bar.setStyleSheet(f"background-color: {AppConfig.CARD_BACKGROUND}; border-bottom: 1px solid #2A2A2A;")
        
        h_layout = QHBoxLayout(top_bar)
        h_layout.setContentsMargins(20, 0, 10, 0)
        h_layout.setSpacing(10)
        
        # Current Page Title
        self.page_title_label = QLabel("Dashboard")
        self.page_title_label.setObjectName("Header")
        h_layout.addWidget(self.page_title_label)
        
        h_layout.addStretch(1)
        
        # User Info (Name and Role)
        user_info_v_layout = QVBoxLayout()
        user_info_v_layout.setSpacing(2)
        user_info_v_layout.setAlignment(Qt.AlignmentFlag.AlignRight)
        
        username_label = QLabel(self.current_user.get('username', 'User'))
        username_label.setFont(QFont(AppConfig.FONT_FAMILY, 11, QFont.Weight.Bold))
        username_label.setStyleSheet(f"color: {AppConfig.TEXT_DEFAULT};")
        
        role_label = QLabel(self.current_role)
        role_label.setStyleSheet(f"color: {AppConfig.PRIMARY_COLOR}; font-size: 9pt;")
        
        user_info_v_layout.addWidget(username_label)
        user_info_v_layout.addWidget(role_label)
        
        h_layout.addLayout(user_info_v_layout)
        
        # Avatar/Icon (Placeholder)
        avatar_label = QLabel()
        avatar_label.setPixmap(get_feather_icon("user", "white", 32).pixmap(QSize(32, 32)))
        avatar_label.setFixedSize(32, 32)
        avatar_label.setStyleSheet(f"border-radius: 16px; background-color: {AppConfig.PRIMARY_COLOR};")
        h_layout.addWidget(avatar_label)
        
        # Logout Button
        logout_button = QToolButton()
        logout_button.setIcon(get_feather_icon("log-out", AppConfig.DANGER_COLOR, 24))
        logout_button.setToolTip("Logout")
        logout_button.setStyleSheet("QToolButton {border: none;}")
        logout_button.clicked.connect(self.logout)
        h_layout.addWidget(logout_button)
        
        return top_bar

    def _initialize_dashboards(self):
        """Instantiates all dashboard widgets and adds them to the stacked widget."""
        
        # Pass the api_client and current_user data as required
        
        # Admin Dashboards
        if self.current_role == "Admin":
            admin_dash = AdminDashboardWidget(api_client=self.api)
            self.stacked_widget.addWidget(admin_dash) # Index 0: Admin Dashboard
            self.stacked_widget.addWidget(admin_dash.user_management_widget) # Index 1: User Management (part of admin)
            self.page_map = {
                "Dashboard": 0,
                "User Management": 1,
                # Placeholders for other Admin pages
                "Product Management": 2, 
                "Category Management": 3,
                "Sales Management": 4,
            }
        
        # Manager Dashboards (Placeholder indices)
        elif self.current_role == "Manager":
            # manager_dash = ManagerDashboardWidget(api_client=self.api)
            # self.stacked_widget.addWidget(manager_dash)
            self.page_map = {
                "Dashboard": 0,
                "Product Management": 1,
                "Category Management": 2,
                "Sales Management": 3,
            }
            # Placeholder widgets for now:
            self.stacked_widget.addWidget(QWidget())
            self.stacked_widget.addWidget(QWidget())
            self.stacked_widget.addWidget(QWidget())
            self.stacked_widget.addWidget(QWidget())

        # Retailer Dashboards (Placeholder indices)
        elif self.current_role == "Retailer":
            # retailer_pos = RetailerDashboardWidget(api_client=self.api)
            # self.stacked_widget.addWidget(retailer_pos)
            self.page_map = {
                "Dashboard": 0,
                "Retailer POS": 1,
            }
            # Placeholder widgets for now:
            self.stacked_widget.addWidget(QWidget())
            self.stacked_widget.addWidget(QWidget())

    def switch_page(self, page_name: str):
        """Switches the view in the QStackedWidget and updates sidebar state."""
        index = self.page_map.get(page_name)
        if index is not None:
            self.stacked_widget.setCurrentIndex(index)
            self.page_title_label.setText(page_name)
            
            # Update button check state
            for name, button in self.nav_buttons.items():
                button.setChecked(name == page_name)
        else:
            print(f"Warning: Page '{page_name}' not found in map.")

    def show_default_page(self):
        """Determines the default landing page based on role."""
        if self.current_role == 'Admin':
            self.switch_page("User Management") # Admin default page
        elif self.current_role == 'Manager':
            self.switch_page("Dashboard")
        elif self.current_role == 'Retailer':
            self.switch_page("Retailer POS")

    def logout(self):
        """Calls the API logout and closes the main window."""
        self.api.logout()
        # Find the parent login window and handle the transition
        from ui.login_window import LoginWindow
        login_window = next((w for w in QApplication.topLevelWidgets() if isinstance(w, LoginWindow)), None)
        if login_window:
            login_window.handle_logout()
        else:
            QApplication.quit()