"""
dashboard_widgets.py
Reusable UI components for StockaDoodle/LogiJex IMS
Includes: ProductCardWidget, BadgeLabel, shared table styling helpers
Used across Admin, Manager, and Retailer dashboards
"""

from PyQt6.QtWidgets import (
    QWidget, QFrame, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QTableWidget, QTableWidgetItem, QScrollArea,
    QGridLayout, QMessageBox, QInputDialog, QHeaderView,
    QSpacerItem, QSizePolicy
)
from PyQt6.QtGui import QPixmap, QFont, QIcon
from PyQt6.QtCore import Qt, QSize, pyqtSignal

import os
from core.inventory_manager import InventoryManager
from core.product_manager import ProductManager
from core.user_manager import UserManager  # Import UserManager for Admin Dashboard
from core.sales_manager import SalesManager  # Add the missing SalesManager import
from core.activity_logger import ActivityLogger  # Import logger
from utils.helpers import get_feather_icon, load_product_image, delete_product_image, save_product_image
from utils.config import AppConfig
from utils.decorators import role_required
from ui.product_management import ProductDialog  # Import ProductDialog for editing
from utils.styles import get_global_stylesheet, get_product_card_style, apply_table_styles, get_dashboard_card_style, get_admin_dashboard_style, get_retailer_dashboard_style  # Import styles


# from ui.sales_management import SalesDialog # Not directly used for "Add Stock" in this context

class ProductCardWidget(QFrame):
    """
    A custom QFrame widget to display a single product as a card.
    """

    def __init__(self, product_data, current_user, parent=None):
        super().__init__(parent)
        self.product_data = product_data
        self.current_user = current_user
        self.product_manager = ProductManager()
        self.activity_logger = ActivityLogger()  # Initialize logger
        
        # Apply card styling
        self.setObjectName("productCard")
        self.setProperty("class", "product-card")
        self.setStyleSheet(get_product_card_style()) # Apply specific product card styling
        
        self.init_ui()
        
        # Set better size for cards
        self.setFixedSize(250, 450)

    def init_ui(self):
        # Setup layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)
        
        # Product image with better container
        image_container = QFrame()
        image_container.setObjectName("image_container")
        image_container.setFixedSize(200, 200)
        image_layout = QVBoxLayout(image_container)
        image_layout.setContentsMargins(0, 0, 0, 0)
        
        self.image_label = QLabel()
        self.image_label.setFixedSize(200, 200)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setScaledContents(True)  # Scale the image to fit the label
        
        image_path = self.product_data.get('image_path')
        pixmap = load_product_image(image_path, target_size=(200, 200), keep_aspect_ratio=True)
        self.image_label.setPixmap(pixmap)
        
        image_layout.addWidget(self.image_label)
        layout.addWidget(image_container, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Product info in a separate stylized container
        info_container = QFrame()
        info_container.setObjectName("infoContainer")
        info_layout = QVBoxLayout(info_container)
        info_layout.setContentsMargins(8, 8, 8, 8)
        info_layout.setSpacing(5)
        
        # Product name with bold styling
        name_label = QLabel(self.product_data.get("name", "N/A"))
        name_label.setProperty("class", "product-title")
        name_label.setWordWrap(True)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_layout.addWidget(name_label)
        
        # Brand
        brand_label = QLabel(f"Brand: {self.product_data.get('brand', 'N/A')}")
        brand_label.setProperty("class", "product-detail")
        brand_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_layout.addWidget(brand_label)
        
        # Price with highlight color
        price = self.product_data.get('price', 0.0)
        price_label = QLabel(f"${price:.2f}")
        price_label.setProperty("class", "product-price")
        price_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_layout.addWidget(price_label)
        
        # Stock with status color
        stock = self.product_data.get('stock', 0)
        min_stock = self.product_data.get('min_stock_level', 5)
        
        if stock <= 0:
            status_text = "No Stock"
            status_class = "status-no-stock"
        elif stock <= min_stock:
            status_text = "Low Stock"
            status_class = "status-low-stock"
        else:
            status_text = "In Stock"
            status_class = "status-in-stock"
        
        stock_label = QLabel(f"Stock: {stock} ({status_text})")
        stock_label.setProperty("class", status_class)
        stock_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_layout.addWidget(stock_label)
        
        # Category
        category = self.product_data.get('category', 'N/A')
        category_label = QLabel(f"Category: {category}")
        category_label.setProperty("class", "product-detail")
        category_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info_layout.addWidget(category_label)
        
        layout.addWidget(info_container)
        
        # Action buttons
        button_layout = QHBoxLayout()
        button_layout.setSpacing(10)
        
        self.add_stock_btn = QPushButton("Add Stock")
        self.add_stock_btn.setIcon(get_feather_icon("plus-square", size=14))
        self.add_stock_btn.clicked.connect(self.add_stock)
        button_layout.addWidget(self.add_stock_btn)

        self.edit_product_btn = QPushButton("Edit")
        self.edit_product_btn.setIcon(get_feather_icon("edit", size=14))
        self.edit_product_btn.clicked.connect(self.edit_product)
        button_layout.addWidget(self.edit_product_btn)
        
        layout.addLayout(button_layout)
        
        self.update_card_visibility_based_on_role()

    # Image is now handled directly in init_ui and update_card_data methods

    def update_card_data(self, new_product_data):
        self.product_data = new_product_data
        
        # Find all child labels and update them
        for child in self.findChildren(QLabel):
            if child.text().startswith("Brand:"):
                child.setText(f"Brand: {new_product_data.get('brand', 'N/A')}")
            elif child.property("class") == "product-title":
                child.setText(new_product_data.get("name", "N/A"))
            elif child.property("class") == "product-price":
                price = new_product_data.get('price', 0.0)
                child.setText(f"${price:.2f}")
            elif "Stock:" in child.text():
                stock = new_product_data.get('stock', 0)
                min_stock = new_product_data.get('min_stock_level', 5)
                
                if stock <= 0:
                    status_text = "No Stock"
                    status_class = "status-no-stock"
                elif stock <= min_stock:
                    status_text = "Low Stock"
                    status_class = "status-low-stock"
                else:
                    status_text = "In Stock"
                    status_class = "status-in-stock"
                
                child.setText(f"Stock: {stock} ({status_text})")
                child.setProperty("class", status_class)
            elif child.text().startswith("Category:"):
                child.setText(f"Category: {new_product_data.get('category', 'N/A')}")
        
        # Update image
        image_path = new_product_data.get('image_path')
        pixmap = load_product_image(image_path, target_size=(200, 200), keep_aspect_ratio=True)
        self.image_label.setPixmap(pixmap)
        
        self.update_card_visibility_based_on_role()  # Re-apply role-based visibility

    def update_card_visibility_based_on_role(self):
        user_role = self.current_user.get("role")
        if user_role == "retailer":
            self.add_stock_btn.hide()
            self.edit_product_btn.hide()
        else:  # admin, manager
            self.add_stock_btn.show()
            self.edit_product_btn.show()

    @role_required(["admin", "manager"])
    def add_stock(self, *args):
        # Ignore any extra positional arguments that might be passed
        # Create a simple input dialog for quantity
        from PyQt6.QtWidgets import QInputDialog
        quantity, ok = QInputDialog.getInt(self, "Add Stock", f"Enter quantity to add for {self.product_data['name']}:",
                                           value=1, min=1, max=1000)

        if ok and quantity > 0:
            current_stock = self.product_data.get("stock", 0)
            new_stock = current_stock + quantity

            success = self.product_manager.update_product(
                self.product_data['id'],
                self.product_data['name'],
                self.product_data['category_id'],
                self.product_data['brand'],
                self.product_data['price'],
                new_stock,
                self.product_data['image_path'],
                self.product_data['expiration_date'],
                self.product_data['min_stock_level']
            )
            if success:
                QMessageBox.information(self, "Stock Updated",
                                        f"Successfully added {quantity} units to {self.product_data['name']}.")
                # Update the card's displayed stock
                self.product_data['stock'] = new_stock
                self.update_card_data(self.product_data)
            else:
                QMessageBox.critical(self, "Error", f"Failed to add stock to {self.product_data['name']}.")

    @role_required(["admin", "manager"])
    def edit_product(self, *args):
        product_id = self.product_data['id']
        product_details = self.product_manager.get_product_by_id(product_id)
        if not product_details:
            QMessageBox.critical(self, "Error", "Product not found for editing.")
            return

        dialog = ProductDialog(product_data=product_details, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_data = dialog.get_product_data()
            if updated_data:
                # Handle image update: delete old if new one selected and different
                old_image_path = product_details.get('image_path')
                new_image_path_from_dialog = updated_data.get('image_path')  # This is the original path or new selected path

                final_image_path_for_db = old_image_path  # Assume no change initially

                if new_image_path_from_dialog and new_image_path_from_dialog != old_image_path:
                    # A new image was selected or existing one was re-selected (need to re-save if it's a temp path)
                    # Check if it's a new file (not already in our assets/product_images)
                    if not new_image_path_from_dialog.startswith(AppConfig.PRODUCT_IMAGE_DIR):
                        saved_image_rel_path = save_product_image(new_image_path_from_dialog)
                        if saved_image_rel_path:
                            final_image_path_for_db = saved_image_rel_path
                            # Delete old image if it exists
                            if old_image_path and os.path.exists(old_image_path):
                                delete_product_image(old_image_path)
                        else:
                            QMessageBox.warning(self, "Image Save Error",
                                                "Could not save new image. Product updated without new image.")
                            final_image_path_for_db = old_image_path  # Revert to old path if new save failed
                    else:
                        # Image was already in the product_images directory, no need to re-save
                        final_image_path_for_db = new_image_path_from_dialog
                elif not new_image_path_from_dialog and old_image_path:  # Image was removed
                    delete_product_image(old_image_path)
                    final_image_path_for_db = None  # Set to None in DB

                success = self.product_manager.update_product(
                    product_id,
                    updated_data['name'],
                    updated_data['category_id'],
                    updated_data['brand'],  # Correct order: brand before price
                    updated_data['price'],
                    updated_data['stock'],
                    final_image_path_for_db,  # Use the final path for DB
                    updated_data['expiration_date'],
                    updated_data['min_stock_level']
                )
                if success:
                    QMessageBox.information(self, "Success", "Product updated successfully.")
                    
                    # Log the product update
                    self.activity_logger.log_activity(
                        user_info=self.current_user,
                        action="PRODUCT_UPDATED",
                        target=updated_data['name'],
                        details={"product_id": product_id}
                    )
                    
                    # Refresh the card with new data
                    self.update_card_data(updated_data)
                else:
                    QMessageBox.critical(self, "Error", "Failed to update product.")

# Add the new class here
class ProductCardDisplay(QWidget):
    """
    A reusable widget to display product cards in a grid layout.
    This can be used in any dashboard to show products in a consistent card style.
    """
    
    def __init__(self, current_user, parent=None, cards_per_row=4, card_width=250, card_height=450):
        super().__init__(parent)
        self.current_user = current_user
        self.product_manager = ProductManager()
        self.cards_per_row = cards_per_row
        self.card_width = card_width
        self.card_height = card_height
        
        # Initialize layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(10)
        
        # Create scroll area for cards
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Container for the grid
        self.container = QWidget()
        self.grid_layout = QGridLayout(self.container)
        self.grid_layout.setContentsMargins(10, 10, 10, 10)
        self.grid_layout.setSpacing(15)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        
        # Set the container in the scroll area
        self.scroll_area.setWidget(self.container)
        self.main_layout.addWidget(self.scroll_area)
        
        # Ensure the scroll area has a minimum height to show at least 2 rows of cards
        min_height = (self.card_height + self.grid_layout.spacing()) * 2 + self.grid_layout.contentsMargins().top() + self.grid_layout.contentsMargins().bottom()
        self.scroll_area.setMinimumHeight(min_height)
        
    def display_products(self, products):
        """
        Display products in a grid layout using ProductCardWidget
        
        Args:
            products (list): List of product dictionaries to display
        """
        # Clear existing product cards
        for i in reversed(range(self.grid_layout.count())):
            widget = self.grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()
        
        # Populate the grid with products
        row = 0
        col = 0
        
        for product in products:
            card = ProductCardWidget(product, self.current_user, parent=self.container)
            card.setFixedSize(self.card_width, self.card_height)
            self.grid_layout.addWidget(card, row, col)
            col += 1
            if col >= self.cards_per_row:
                col = 0
                row += 1
        
        # Add a stretch to the last row and column to push items to top-left
        if self.grid_layout.columnCount() > 0:
            self.grid_layout.setColumnStretch(self.grid_layout.columnCount(), 1)
        if self.grid_layout.rowCount() > 0:
            self.grid_layout.setRowStretch(self.grid_layout.rowCount(), 1)
        
        # If no products, show a message
        if not products:
            no_products_label = QLabel("No products found.")
            no_products_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_products_label.setStyleSheet("font-size: 14pt; color: rgba(255,255,255,0.5); padding: 20px;")
            self.grid_layout.addWidget(no_products_label, 0, 0, 1, self.cards_per_row)
    
    def set_cards_per_row(self, count):
        """Change the number of cards per row"""
        self.cards_per_row = count
    
    def set_card_size(self, width, height):
        """Change the size of each card"""
        self.card_width = width
        self.card_height = height

class AdminDashboardWidget(QWidget):
    def __init__(self, current_user, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.inventory_manager = InventoryManager()
        self.product_manager = ProductManager()  
        self.user_manager = UserManager()  
        self.sales_manager = SalesManager()
        self.activity_logger = ActivityLogger()  # Use consistent naming

        # Use centralized styling
        self.setStyleSheet(get_admin_dashboard_style())
        
        self.init_ui()
        self.load_dashboard_data()

    def init_ui(self):
        # Create a main layout for the entire widget
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create a scroll area using our custom class
        scroll_area = DashboardScrollArea()
        
        # Create content widget for scroll area
        content_widget = QWidget()
        
        # Content layout
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        content_layout.setSpacing(20)

        # Welcome Message with more appealing style
        welcome_container = QWidget()
        welcome_container.setObjectName("welcomeFrame")
        welcome_container.setStyleSheet(f"""
            #welcomeFrame {{
                background-color: {AppConfig.PRIMARY_COLOR}; 
                border-radius: 10px;
            }}
        """)
        welcome_layout = QVBoxLayout(welcome_container)
        welcome_layout.setContentsMargins(15, 15, 15, 15)
        
        welcome_label = QLabel(
            f"Welcome, {self.current_user.get('username')} ({self.current_user.get('role').capitalize()})!")
        welcome_label.setFont(QFont(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_XLARGE, QFont.Weight.Bold))
        welcome_label.setStyleSheet("color: white;")
        welcome_layout.addWidget(welcome_label)
        
        # Add current date
        from datetime import datetime
        date_label = QLabel(f"Today: {datetime.now().strftime('%A, %B %d, %Y')}")
        date_label.setStyleSheet("color: rgba(255,255,255,0.8);")
        welcome_layout.addWidget(date_label)
        
        content_layout.addWidget(welcome_container)

        # Dashboard Overview Section (Metrics Cards)
        metrics_section = QFrame()
        metrics_section.setProperty("class", "dashboard-section")
        metrics_layout = QVBoxLayout(metrics_section)
        metrics_layout.setContentsMargins(15, 15, 15, 15)
        
        metrics_header = QLabel("Dashboard Overview")
        metrics_header.setProperty("heading", "true")
        metrics_layout.addWidget(metrics_header)
        
        # Create a horizontal layout for metric cards with good sizing
        metrics_cards_layout = QHBoxLayout()
        metrics_cards_layout.setSpacing(15)
        
        # Create cards and add them to the horizontal layout - only admin-relevant metrics
        self.total_products_card = self._create_summary_card("Total Products", "package")
        self.total_users_card = self._create_summary_card("Total Users", "users")
        self.total_sales_card = self._create_summary_card("Total Sales", "dollar-sign")
        
        # Apply size policies to ensure cards resize properly
        for card in [self.total_products_card, self.total_users_card, self.total_sales_card]:
            card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        metrics_cards_layout.addWidget(self.total_products_card)
        metrics_cards_layout.addWidget(self.total_users_card)
        metrics_cards_layout.addWidget(self.total_sales_card)
        
        metrics_layout.addLayout(metrics_cards_layout)
        content_layout.addWidget(metrics_section)
        
        # User Logs Section - Enhanced as the primary focus for Admin
        logs_section = QFrame()
        logs_section.setProperty("class", "dashboard-section")
        logs_layout = QVBoxLayout(logs_section)
        logs_layout.setContentsMargins(15, 15, 15, 15)
        
        logs_header = QLabel("User Activity Logs")
        logs_header.setProperty("heading", "true")
        logs_header.setFont(QFont(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_XLARGE, QFont.Weight.Bold))
        logs_header.setStyleSheet(f"color: {AppConfig.SECONDARY_COLOR}; margin-bottom: 10px;")
        logs_layout.addWidget(logs_header)
        
        # User logs instruction label
        logs_description = QLabel("This section displays all user activities across the system. Monitor staff actions and system usage.")
        logs_description.setStyleSheet("color: rgba(255,255,255,0.8); margin-bottom: 15px;")
        logs_description.setWordWrap(True)
        logs_layout.addWidget(logs_description)
        
        # User logs table with enhanced design
        self.user_logs_table = QTableWidget()
        self.user_logs_table.setColumnCount(4)
        self.user_logs_table.setHorizontalHeaderLabels(["User", "Action", "Target", "Timestamp"])
        
        # Apply consistent table styling
        from utils.styles import apply_table_styles
        apply_table_styles(self.user_logs_table)
        
        # Set minimum height for the table
        self.user_logs_table.setMinimumHeight(500)
        
        logs_layout.addWidget(self.user_logs_table)
        content_layout.addWidget(logs_section)
        
        content_layout.addStretch()  # Push content to top

        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

    def _create_summary_card(self, title, icon_name):
        # Colors for different card types based on the title
        bg_colors = {
            "Total Products": AppConfig.PRODUCTS_CARD_COLOR,
            "Total Users": AppConfig.USERS_CARD_COLOR, 
            "Total Sales": AppConfig.SALES_CARD_COLOR,
        }
        
        # Default color if title not in our mapping
        card_color = bg_colors.get(title, AppConfig.PRIMARY_COLOR)
        
        card = QFrame()
        card.setProperty("class", "dashboard-card") # For styling via stylesheet
        card.setMaximumHeight(150)
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        
        # Apply specific card styling with gradient background based on color
        card.setStyleSheet(get_dashboard_card_style(card_color))
        
        card_layout = QVBoxLayout(card)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.setSpacing(8)

        # Icon and title in a horizontal layout
        header_layout = QHBoxLayout()
        icon_label = QLabel()
        icon_label.setPixmap(get_feather_icon(icon_name, "white", 24).pixmap(24, 24))
        header_layout.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignLeft)
        
        title_label = QLabel(title)
        title_label.setProperty("class", "card-title")
        header_layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignLeft)
        header_layout.addStretch()
        card_layout.addLayout(header_layout)

        # Value with big font
        value_label = QLabel("N/A")
        value_label.setProperty("class", "card-value")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        card_layout.addWidget(value_label)
        
        # Store reference to update later
        card.value_label = value_label
        return card

    def load_dashboard_data(self):
        """Load all data for the admin dashboard, focusing on administrative metrics and user logs"""
        # Total Products
        all_products = self.product_manager.get_products()[:100]  # Limit to 100 products
        self.total_products_card.value_label.setText(str(len(all_products)))

        # Total Users
        all_users = self.user_manager.get_all_users()
        if all_users:
            self.total_users_card.value_label.setText(str(len(all_users)))
        else:
            self.total_users_card.value_label.setText("0")
        
        # Total Sales - Calculate total sales amount
        from datetime import datetime, timedelta
        from PyQt6.QtCore import QDate
        
        # Use date range of last 30 days for a reasonable sample
        end_date = QDate.currentDate()
        start_date = end_date.addDays(-30)
        
        sales_data = self.sales_manager.get_sales_reports(start_date, end_date)
        if sales_data:
            total_sales_amount = sum(float(sale['total_price']) for sale in sales_data)
            self.total_sales_card.value_label.setText(f"${total_sales_amount:.2f}")
        else:
            self.total_sales_card.value_label.setText("$0.00")
        
        # Load user logs data from the ActivityLogger - the primary focus for Admin
        self._load_user_logs()

    def _load_user_logs(self):
        """Load user activity logs from the logger - comprehensive view for Admin"""
        # Clear existing rows
        self.user_logs_table.setRowCount(0)
        
        # Fetch real logs from ActivityLogger (most recent first)
        logs = self.activity_logger.get_logs(limit=100)  # Get latest 100 logs
        
        if not logs:
            # If no logs found, add a message row
            self.user_logs_table.setRowCount(1)
            no_logs_item = QTableWidgetItem("No activity logs found")
            self.user_logs_table.setSpan(0, 0, 1, 4)  # Span all columns
            self.user_logs_table.setItem(0, 0, no_logs_item)
            return
            
        self.user_logs_table.setRowCount(len(logs))
        
        from utils.styles import apply_table_styles
        apply_table_styles(self.user_logs_table)
        
        # Configure column sizing
        header = self.user_logs_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)  # User
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Action
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)           # Target
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Timestamp
        
        # Set minimum column widths to ensure visibility
        self.user_logs_table.setColumnWidth(0, 150)  # User
        self.user_logs_table.setColumnWidth(1, 200)  # Action
        self.user_logs_table.setColumnWidth(3, 200)  # Timestamp
        
        for row, log in enumerate(logs):
            # Parse timestamp for better display
            import datetime
            try:
                timestamp = datetime.datetime.fromisoformat(log['timestamp'])
                timestamp_str = timestamp.strftime("%Y-%m-%d %H:%M")
            except:
                timestamp_str = log['timestamp']
                
            # Create table items with larger font
            username_item = QTableWidgetItem(log.get('username', 'Unknown'))
            action_item = QTableWidgetItem(log.get('action', 'Unknown Action'))
            target_item = QTableWidgetItem(log.get('target', 'N/A'))
            timestamp_item = QTableWidgetItem(timestamp_str)
            
            # Apply styling based on action type
            if "Login" in log.get('action', '') or "Logged In" in log.get('action', ''):
                action_item.setForeground(Qt.GlobalColor.green)
            elif "Added" in log.get('action', ''):
                action_item.setForeground(Qt.GlobalColor.blue)
            elif "Deleted" in log.get('action', ''):
                action_item.setForeground(Qt.GlobalColor.red)
            elif "Edited" in log.get('action', '') or "Modified" in log.get('action', ''):
                action_item.setForeground(Qt.GlobalColor.yellow)
            
            # Set the items in the table
            self.user_logs_table.setItem(row, 0, username_item)
            self.user_logs_table.setItem(row, 1, action_item)
            self.user_logs_table.setItem(row, 2, target_item)
            self.user_logs_table.setItem(row, 3, timestamp_item)

# DashboardScrollArea for consistent scrolling across dashboard widgets
class DashboardScrollArea(QScrollArea):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setFrameShape(QFrame.Shape.NoFrame)
        
        # Apply global stylesheet (the scrollbar styling is included in get_global_stylesheet)
        # No need for local styling since it's handled by the global stylesheet

class ManagerDashboardWidget(QWidget):
    """Manager Dashboard with inventory alerts and product management sections."""
    
    def __init__(self, current_user, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.inventory_manager = InventoryManager()
        self.product_manager = ProductManager()
        self.sales_manager = SalesManager()
        self.user_manager = UserManager()
        self.activity_logger = ActivityLogger()
        self.all_products = []  # Cache all products for filtering

        # Update manager dashboard with a softer, operation-focused blue color scheme
        self.setStyleSheet(f"""
            QWidget {{
                background-color: #2a3f5f;  /* Softer blue background for manager */
                color: {AppConfig.TEXT_COLOR};
                font-family: {AppConfig.FONT_FAMILY};
                font-size: {AppConfig.FONT_SIZE_NORMAL}pt;
            }}
            QLabel {{
                color: #e8f0ff;  /* Slightly blue-tinted text */
            }}
            QLineEdit, QComboBox {{
                background-color: #3a506b;  /* Lighter blue for inputs */
                border: 1px solid #5e80b0;  /* Blue border */
                border-radius: 5px;
                padding: 5px;
                color: white;
            }}
            QComboBox::drop-down {{
                border: 0px;
            }}
            QComboBox::down-arrow {{
                image: url(assets/icons/chevron-down.png);
                width: 16px;
                height: 16px;
            }}
            QPushButton {{
                background-color: #3781d8;  /* Bright blue buttons */
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-size: {AppConfig.FONT_SIZE_NORMAL}pt;
            }}
            QPushButton:hover {{
                background-color: #4393e6;  /* Lighter blue on hover */
            }}
            QScrollArea {{
                border: 1px solid #4a7cbd;
                border-radius: 8px;
                background-color: transparent;
            }}
            QScrollBar:vertical {{
                border: none;
                background: rgba(0, 0, 0, 0.1);
                width: 10px;
                margin: 0px;
            }}
            QScrollBar::handle:vertical {{
                background: #4a7cbd;
                min-height: 20px;
                border-radius: 5px;
            }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
                height: 0px;
            }}
            #managerCard, .manager-card {{
                background-color: #3a506b;  /* Consistent blue for manager cards */
                border: 1px solid #5e80b0;
                border-radius: 8px;
                padding: 15px;
                margin: 10px;
                min-width: 180px;  /* Wider cards */
            }}
            #managerTitle {{
                color: #78a9ff;  /* Brighter blue for titles */
                font-size: {AppConfig.FONT_SIZE_XLARGE}pt;
                font-weight: bold;
                margin-bottom: 10px;
            }}
            QTableWidget {{
                background-color: #2c3e50;
                color: {AppConfig.TEXT_COLOR};
                border: 1px solid #4a7cbd;
                gridline-color: #555;
                border-radius: 6px;
            }}
            QHeaderView::section {{
                background-color: #3781d8;  /* Bright blue header */
                color: white;
                padding: 8px;  /* Taller header */
                border: none;
                border-right: 1px solid #5e80b0;
                border-bottom: 1px solid #5e80b0;
                font-weight: bold;
            }}
            QTableWidget::item {{
                padding: 6px;
            }}
        """)
        self.init_ui()
        self.load_dashboard_data()

    def init_ui(self):
        # Create a main layout for the entire widget
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Create a scroll area using our custom class
        scroll_area = DashboardScrollArea()
        scroll_area.setWidgetResizable(True)  # Ensure it's resizable
        
        # Create content widget for scroll area
        content_widget = QWidget()
        
        # Content layout
        content_layout = QVBoxLayout(content_widget)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        content_layout.setSpacing(20)

        # Welcome Message with more appealing style
        welcome_container = QWidget()
        welcome_container.setStyleSheet(f"""
            background-color: #4a7cbd; 
            border-radius: 10px; 
            padding: 10px;
        """)
        welcome_layout = QVBoxLayout(welcome_container)
        
        welcome_label = QLabel(
            f"Welcome, {self.current_user.get('username')} ({self.current_user.get('role').capitalize()})!")
        welcome_label.setFont(QFont(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_XLARGE, QFont.Weight.Bold))
        welcome_label.setStyleSheet("color: white;")
        welcome_layout.addWidget(welcome_label)
        
        content_layout.addWidget(welcome_container)

        # Summary Cards - improved styling
        summary_title = QLabel("Dashboard Overview")
        summary_title.setFont(QFont(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_LARGE, QFont.Weight.Bold))
        summary_title.setStyleSheet("color: #78a9ff; margin-top: 10px;")
        content_layout.addWidget(summary_title)
        
        summary_layout = QHBoxLayout()
        summary_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        summary_layout.setSpacing(20)

        self.total_products_card = self._create_summary_card("Total Products", "package")
        self.total_sales_card = self._create_summary_card("Total Sales", "dollar-sign")
        self.low_stock_card = self._create_summary_card("Low Stock Items", "alert-triangle")
        self.expiring_items_card = self._create_summary_card("Expiring Soon", "calendar")

        summary_layout.addWidget(self.total_products_card)
        summary_layout.addWidget(self.total_sales_card)
        summary_layout.addWidget(self.low_stock_card)
        summary_layout.addWidget(self.expiring_items_card)
        summary_layout.addStretch()  # Push cards to left

        content_layout.addLayout(summary_layout)

        # Low Stock and Expiring Items Tables - Wrapped in a Section with improved styling
        section_title = QLabel("Inventory Alerts")
        section_title.setFont(QFont(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_LARGE, QFont.Weight.Bold))
        section_title.setStyleSheet("color: #78a9ff; margin-top: 20px;")
        content_layout.addWidget(section_title)
        
        reports_layout = QHBoxLayout()
        reports_layout.setSpacing(20)

        # Low Stock Table - improved styling
        low_stock_group = QFrame()
        low_stock_group.setFrameShape(QFrame.Shape.StyledPanel)
        low_stock_group.setFrameShadow(QFrame.Shadow.Raised)
        low_stock_group.setStyleSheet(f"""
            QFrame {{
                background-color: #3f5161;
                border: 2px solid #ff9f43; /* Orange for low stock warning */
                border-radius: 8px;
                padding: 10px;
            }}
            QLabel {{
                color: white;
                font-weight: bold;
                font-size: {AppConfig.FONT_SIZE_LARGE}pt;
            }}
            QTableWidget {{
                background-color: #2c3e50;
                color: white;
                border: 1px solid #4a7cbd;
                gridline-color: #555;
                font-size: {AppConfig.FONT_SIZE_NORMAL}pt;
            }}
            QHeaderView::section {{
                background-color: #3781d8;
                color: white;
                padding: 8px;
                border: none;
                border-right: 1px solid #5e80b0;
                border-bottom: 1px solid #5e80b0;
                font-weight: bold;
            }}
            QTableWidget::item {{
                padding: 8px;
            }}
        """)
        low_stock_layout = QVBoxLayout(low_stock_group)
        
        low_stock_header = QLabel("Low Stock Items")
        low_stock_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        low_stock_layout.addWidget(low_stock_header)
        
        self.low_stock_table = QTableWidget()
        self.low_stock_table.setColumnCount(4)  # Added brand column
        self.low_stock_table.setHorizontalHeaderLabels(["Product Name", "Brand", "Current Stock", "Min Level"])
        
        # Make the table taller for better visibility
        self.low_stock_table.setMinimumHeight(200)
        self.low_stock_table.setMaximumHeight(200)  # Limit height to fit in view
        
        # Set larger default font size for cells
        font = QFont(AppConfig.FONT_FAMILY, int(AppConfig.FONT_SIZE_NORMAL * 1.2))
        self.low_stock_table.setFont(font)
        
        # Improve visibility for all content
        self.low_stock_table.verticalHeader().setDefaultSectionSize(50)  # Taller rows
        
        # Set up header to auto-adjust based on content
        header = self.low_stock_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Product name stretches
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Brand
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Stock
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)  # Min level
        
        # Set larger font for header
        header_font = QFont(AppConfig.FONT_FAMILY, int(AppConfig.FONT_SIZE_NORMAL * 1.2), QFont.Weight.Bold)
        self.low_stock_table.horizontalHeader().setFont(header_font)
        
        low_stock_layout.addWidget(self.low_stock_table)
        reports_layout.addWidget(low_stock_group)

        # Expiring Items Table - improved styling
        expiring_group = QFrame()
        expiring_group.setFrameShape(QFrame.Shape.StyledPanel)
        expiring_group.setFrameShadow(QFrame.Shadow.Raised)
        expiring_group.setStyleSheet(f"""
            QFrame {{
                background-color: #3f5161;
                border: 2px solid #e84393; /* Pink/purple for expiring */
                border-radius: 8px;
                padding: 10px;
            }}
            QLabel {{
                color: white;
                font-weight: bold;
                font-size: {AppConfig.FONT_SIZE_LARGE}pt;
            }}
            QTableWidget {{
                background-color: #2c3e50;
                color: white;
                border: 1px solid #4a7cbd;
                gridline-color: #555;
                font-size: {AppConfig.FONT_SIZE_NORMAL}pt;
            }}
            QHeaderView::section {{
                background-color: #3781d8;
                color: white;
                padding: 8px;
                border: none;
                border-right: 1px solid #5e80b0;
                border-bottom: 1px solid #5e80b0;
                font-weight: bold;
            }}
            QTableWidget::item {{
                padding: 8px;
            }}
        """)
        
        expiring_layout = QVBoxLayout(expiring_group)
        
        expiring_header = QLabel("Expiring Items (Next 7 Days)")
        expiring_header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        expiring_layout.addWidget(expiring_header)
        
        self.expiring_table = QTableWidget()
        self.expiring_table.setColumnCount(3)  # Added brand column
        self.expiring_table.setHorizontalHeaderLabels(["Product Name", "Brand", "Expiration Date"])
        
        # Make the table taller for better visibility
        self.expiring_table.setMinimumHeight(200)
        self.expiring_table.setMaximumHeight(200)  # Limit height to fit in view
        
        # Set the same font as low_stock_table
        self.expiring_table.setFont(font)  # Reuse the font defined above
        
        # Improve visibility for all content
        self.expiring_table.verticalHeader().setDefaultSectionSize(50)  # Taller rows
        
        # Set up header to auto-adjust based on content
        header = self.expiring_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)  # Product name stretches
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)  # Brand
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)  # Expiration date
        
        # Set larger font for header
        self.expiring_table.horizontalHeader().setFont(header_font)  # Same header font
        
        expiring_layout.addWidget(self.expiring_table)
        reports_layout.addWidget(expiring_group)

        content_layout.addLayout(reports_layout)

        # Product Management Section - Added clear separation and improved styling
        products_section = QWidget()
        products_section_layout = QVBoxLayout(products_section)
        products_section_layout.setContentsMargins(0, 30, 0, 50)  # Add top and bottom margin for separation
        
        products_header = QLabel("Product Management")
        products_header.setFont(QFont(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_LARGE, QFont.Weight.Bold))
        products_header.setStyleSheet("color: #78a9ff;")
        products_section_layout.addWidget(products_header)

        # Product Display Area - improved filter section
        filter_container = QFrame()
        filter_container.setStyleSheet(f"""
            background-color: #3a506b;
            border-radius: 8px;
            padding: 10px;
        """)
        filter_layout = QVBoxLayout(filter_container)
        
        filter_header = QLabel("Filter & Sort Products")
        filter_header.setStyleSheet("font-weight: bold; color: white;")
        filter_layout.addWidget(filter_header)
        
        filter_controls = QHBoxLayout()
        filter_controls.setSpacing(10)

        # Search
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search:"))
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Product name or category...")
        self.search_input.textChanged.connect(self.apply_filters_and_sort)
        self.search_input.setStyleSheet("""
            padding: 5px;
            border-radius: 5px;
        """)
        search_layout.addWidget(self.search_input)
        filter_controls.addLayout(search_layout)

        # Category Filter
        filter_controls.addWidget(QLabel("Category:"))
        self.category_filter_combo = QComboBox()
        self.category_filter_combo.addItem("All Categories", None)
        self.category_filter_combo.currentIndexChanged.connect(self.apply_filters_and_sort)
        filter_controls.addWidget(self.category_filter_combo)

        # Brand Filter
        filter_controls.addWidget(QLabel("Brand:"))
        self.brand_filter_combo = QComboBox()
        self.brand_filter_combo.addItem("All Brands", None)
        self.brand_filter_combo.currentIndexChanged.connect(self.apply_filters_and_sort)
        filter_controls.addWidget(self.brand_filter_combo)

        # Stock Filter
        filter_controls.addWidget(QLabel("Stock:"))
        self.stock_filter_combo = QComboBox()
        self.stock_filter_combo.addItem("All Stock", None)
        self.stock_filter_combo.addItem("Low Stock (< Min Level)", "low")
        self.stock_filter_combo.addItem("In Stock (>= Min Level)", "in_stock")
        self.stock_filter_combo.currentIndexChanged.connect(self.apply_filters_and_sort)
        filter_controls.addWidget(self.stock_filter_combo)
        
        filter_layout.addLayout(filter_controls)
        
        # Sort controls in a separate row
        sort_layout = QHBoxLayout()
        sort_layout.addWidget(QLabel("Sort By:"))
        self.sort_combo = QComboBox()
        self.sort_combo.addItem("Name (A-Z)", "name_asc")
        self.sort_combo.addItem("Name (Z-A)", "name_desc")
        self.sort_combo.addItem("Price (Low to High)", "price_asc")
        self.sort_combo.addItem("Price (High to Low)", "price_desc")
        self.sort_combo.addItem("Stock (Low to High)", "stock_asc")
        self.sort_combo.addItem("Stock (High to Low)", "stock_desc")
        self.sort_combo.currentIndexChanged.connect(self.apply_filters_and_sort)
        sort_layout.addWidget(self.sort_combo)
        
        sort_layout.addStretch()  # Push controls to left
        filter_layout.addLayout(sort_layout)
        
        products_section_layout.addWidget(filter_container)

        # Product Cards Grid - set to 4 cards per row with improved scrolling
        product_grid_scroll = QScrollArea()
        product_grid_scroll.setWidgetResizable(True)
        product_grid_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        self.products_container = QWidget()
        self.products_grid_layout = QGridLayout(self.products_container)
        self.products_grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.products_grid_layout.setSpacing(15)  # Spacing between cards
        
        # Ensure the grid layout has enough space to grow
        self.products_container.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        product_grid_scroll.setWidget(self.products_container)
        products_section_layout.addWidget(product_grid_scroll)
        
        # Ensure this section takes up remaining space
        products_section.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        content_layout.addWidget(products_section)

        # Add empty space at the bottom to ensure everything is scrollable
        spacer = QWidget()
        spacer.setFixedHeight(20)  # Bottom padding
        content_layout.addWidget(spacer)

        # Give the content widget a min height to ensure scrolling works properly
        content_widget.setMinimumHeight(2500)  # Higher value to ensure full scrolling
        
        # Make sure the product grid scroll expands to fill available space
        product_grid_scroll.setMinimumHeight(1000)  # Taller product grid to show at least 2 rows

        scroll_area.setWidget(content_widget)
        main_layout.addWidget(scroll_area)

    def _create_summary_card(self, title, icon_name):
        card = QFrame()
        card.setObjectName("managerCard")
        card.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)  # Make cards responsive
        
        # Different card styling for different card types
        if title == "Total Sales":
            card.setStyleSheet("""
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                      stop:0 #3a7bd5, 
                                      stop:1 #5a96e3);
                border-radius: 10px;
                padding: 15px;
                margin: 10px;
                min-width: 150px;
                border: 1px solid rgba(255,255,255,0.2);
            """)
        elif title == "Total Products":
            card.setStyleSheet("""
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                      stop:0 #58b19f, 
                                      stop:1 #79d1bd);
                border-radius: 10px;
                padding: 15px;
                margin: 10px;
                min-width: 150px;
                border: 1px solid rgba(255,255,255,0.2);
            """)
        elif title == "Low Stock Items":
            card.setStyleSheet("""
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                      stop:0 #e58e26, 
                                      stop:1 #f8ab37);
                border-radius: 10px;
                padding: 15px;
                margin: 10px;
                min-width: 150px;
                border: 1px solid rgba(255,255,255,0.2);
            """)
        elif title == "Expiring Soon":
            card.setStyleSheet("""
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                      stop:0 #b36bae, 
                                      stop:1 #d687d3);
                border-radius: 10px;
                padding: 15px;
                margin: 10px;
                min-width: 150px;
                border: 1px solid rgba(255,255,255,0.2);
            """)
        else:
            card.setStyleSheet("""
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0, 
                                      stop:0 #4a7cbd, 
                                      stop:1 #6a9cdd);
                border-radius: 10px;
                padding: 15px;
                margin: 10px;
                min-width: 150px;
                border: 1px solid rgba(255,255,255,0.2);
            """)
        
        card_layout = QVBoxLayout(card)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        icon_label = QLabel()
        icon_label.setPixmap(get_feather_icon(icon_name, "white", 32).pixmap(32, 32))
        card_layout.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignCenter)

        title_label = QLabel(title)
        title_label.setStyleSheet("color: white; font-weight: bold;")
        card_layout.addWidget(title_label, alignment=Qt.AlignmentFlag.AlignCenter)

        value_label = QLabel("N/A")
        value_label.setObjectName("value")
        value_label.setStyleSheet("color: white; font-size: 22pt; font-weight: bold;")
        card_layout.addWidget(value_label, alignment=Qt.AlignmentFlag.AlignCenter)
        card.value_label = value_label  # Store reference to update later
        return card

    def load_dashboard_data(self):
        # Total Products
        all_products = self.product_manager.get_products()[:100]  # Limit to 100 products
        self.total_products_card.value_label.setText(str(len(all_products)))
        
        # Total Sales - Calculate total sales amount
        from datetime import datetime, timedelta
        from PyQt6.QtCore import QDate
        
        # Use date range of last 30 days
        end_date = QDate.currentDate()
        start_date = end_date.addDays(-30)
        
        sales_data = self.sales_manager.get_sales_reports(start_date, end_date)
        total_sales_amount = sum(float(sale['total_price']) for sale in sales_data)
        self.total_sales_card.value_label.setText(f"${total_sales_amount:.2f}")

        # Low Stock Items
        low_stock_items = self.inventory_manager.get_low_stock_items()[:20]  # Limit to 20 items
        self.low_stock_card.value_label.setText(str(len(low_stock_items)))
        self.low_stock_table.setRowCount(len(low_stock_items))
        
        for row, item in enumerate(low_stock_items):
            name_item = QTableWidgetItem(item['name'])
            brand_item = QTableWidgetItem(item.get('brand', 'N/A'))
            stock_item = QTableWidgetItem(str(item['stock']))
            min_stock_item = QTableWidgetItem(str(item['min_stock_level']))
            
            # Set font size larger for better readability
            font = name_item.font()
            font.setPointSize(12)  # Larger font
            name_item.setFont(font)
            brand_item.setFont(font)
            stock_item.setFont(font)
            min_stock_item.setFont(font)
            
            # Apply styling based on stock level
            if item['stock'] <= 0:
                stock_item.setForeground(Qt.GlobalColor.red)
                name_item.setForeground(Qt.GlobalColor.red)
            elif item['stock'] <= item['min_stock_level'] // 2:
                stock_item.setForeground(Qt.GlobalColor.yellow)
            
            self.low_stock_table.setItem(row, 0, name_item)
            self.low_stock_table.setItem(row, 1, brand_item)
            self.low_stock_table.setItem(row, 2, stock_item)
            self.low_stock_table.setItem(row, 3, min_stock_item)
        
        # Expiring Items
        expiring_items = self.inventory_manager.get_expiring_items(days_threshold=7)[:20]  # Limit to 20 items
        self.expiring_items_card.value_label.setText(str(len(expiring_items)))
        self.expiring_table.setRowCount(len(expiring_items))
        
        from datetime import datetime
        current_date = datetime.now().date()
        
        for row, item in enumerate(expiring_items):
            name_item = QTableWidgetItem(item['name'])
            brand_item = QTableWidgetItem(item.get('brand', 'N/A'))
            
            # Set font size larger for better readability
            name_item.setFont(font)
            brand_item.setFont(font)
            
            # Format and highlight expiration date
            expiration_date = item.get('expiration_date', '')
            exp_date_item = QTableWidgetItem("N/A")
            
            if expiration_date:
                exp_date_item = QTableWidgetItem(str(expiration_date))
                exp_date_item.setFont(font)
                
                # Try to calculate days until expiration for color highlighting
                try:
                    if isinstance(expiration_date, str):
                        exp_date_obj = datetime.strptime(expiration_date, "%Y-%m-%d").date()
                    else:
                        exp_date_obj = expiration_date
                    
                    days_until_expiry = (exp_date_obj - current_date).days
                    
                    # Color code based on days until expiration
                    if days_until_expiry <= 3:
                        exp_date_item.setForeground(Qt.GlobalColor.red)
                        name_item.setForeground(Qt.GlobalColor.red)
                    elif days_until_expiry <= 5:
                        exp_date_item.setForeground(Qt.GlobalColor.yellow)
                except Exception:
                    # If date parsing fails, just show without color
                    pass
            
            self.expiring_table.setItem(row, 0, name_item)
            self.expiring_table.setItem(row, 1, brand_item)
            self.expiring_table.setItem(row, 2, exp_date_item)
        
        # Also refresh the product cards
        self.all_products = self.product_manager.get_products()[:100]  # Limit to 100 products
        self.refresh_products_display()
        self.load_brands()  # Load brands for filtering

    def load_categories(self):
        # Only proceed if the combo box exists
        if hasattr(self, 'category_filter_combo'):
            categories = self.product_manager.get_categories()
            self.category_filter_combo.clear()
            self.category_filter_combo.addItem("All Categories", None)
            for cat in categories:
                self.category_filter_combo.addItem(cat['name'], cat['id'])

    def load_brands(self):
        # Only proceed if the combo box exists
        if hasattr(self, 'brand_filter_combo'):
            # Fetch all unique brands from products
            all_products = self.product_manager.get_products()
            brands = sorted(list(set(p.get('brand') for p in all_products if p.get('brand'))))

            self.brand_filter_combo.clear()
            self.brand_filter_combo.addItem("All Brands", None)
            for brand in brands:
                self.brand_filter_combo.addItem(brand, brand)

    def refresh_products_display(self):
        """
        Fetches all products and then applies current filters and sort order.
        """
        # Limit the number of products to prevent stack overflow
        self.all_products = self.product_manager.get_products()[:100]  # Limit to 100 products
        self.apply_filters_and_sort()
        self.load_categories()  # Refresh categories in case new ones were added/removed

    def apply_filters_and_sort(self):
        # Clear existing product cards
        for i in reversed(range(self.products_grid_layout.count())):
            widget = self.products_grid_layout.itemAt(i).widget()
            if widget:
                widget.setParent(None)
                widget.deleteLater()

        filtered_products = list(self.all_products)  # Start with all products

        # Apply Search Filter
        search_term = self.search_input.text().strip().lower()
        if search_term:
            filtered_products = [p for p in filtered_products if
                                 search_term in p.get('name', '').lower() or
                                 search_term in p.get('category', '').lower()]

        # Apply Category Filter
        selected_category_id = self.category_filter_combo.currentData()
        if selected_category_id is not None:
            filtered_products = [p for p in filtered_products if p.get('category_id') == selected_category_id]

        # Apply Brand Filter
        selected_brand = self.brand_filter_combo.currentData()
        if selected_brand is not None:
            filtered_products = [p for p in filtered_products if p.get('brand') == selected_brand]

        # Apply Stock Filter
        stock_filter_type = self.stock_filter_combo.currentData()
        if stock_filter_type == "low":
            filtered_products = [p for p in filtered_products if p.get('stock', 0) <= p.get('min_stock_level', 0)]
        elif stock_filter_type == "in_stock":
            filtered_products = [p for p in filtered_products if p.get('stock', 0) > p.get('min_stock_level', 0)]

        # Apply Sorting
        sort_order = self.sort_combo.currentData()
        if sort_order == "name_asc":
            filtered_products.sort(key=lambda p: p.get('name', '').lower())
        elif sort_order == "name_desc":
            filtered_products.sort(key=lambda p: p.get('name', '').lower(), reverse=True)
        elif sort_order == "price_asc":
            filtered_products.sort(key=lambda p: p.get('price', 0.0))
        elif sort_order == "price_desc":
            filtered_products.sort(key=lambda p: p.get('price', 0.0), reverse=True)
        elif sort_order == "stock_asc":
            filtered_products.sort(key=lambda p: p.get('stock', 0))
        elif sort_order == "stock_desc":
            filtered_products.sort(key=lambda p: p.get('stock', 0), reverse=True)

        # Limit display to max 50 products to avoid stack overflow
        filtered_products = filtered_products[:50]

        # Populate the grid with filtered and sorted products
        # Use ProductCardWidget for display
        max_cols = 4  # 4 cards per row for better utilization of horizontal space
        row = 0
        col = 0
        
        for product in filtered_products:
            card = ProductCardWidget(product, self.current_user, parent=self.products_container)
            # Use consistent size for all cards
            card.setFixedSize(250, 450)
            self.products_grid_layout.addWidget(card, row, col)
            col += 1
            if col >= max_cols:
                col = 0
                row += 1

        # Add a stretch to the last row and column to push items to top-left
        if self.products_grid_layout.columnCount() > 0:
            self.products_grid_layout.setColumnStretch(self.products_grid_layout.columnCount(), 1)
        if self.products_grid_layout.rowCount() > 0:
            self.products_grid_layout.setRowStretch(self.products_grid_layout.rowCount(), 1)

class RetailerDashboardWidget(QWidget):
    """Retailer Dashboard widget implementation."""
    
    def __init__(self, current_user, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.product_manager = ProductManager()
        self.inventory_manager = InventoryManager()
        self.sales_manager = SalesManager()
        self.activity_logger = ActivityLogger()
        self.cart = {}  # {product_id: {'product_data': {}, 'quantity': int}}

        self.setStyleSheet(f"""
            QWidget {{
                background-color: {AppConfig.BACKGROUND_COLOR};
                color: {AppConfig.TEXT_COLOR};
                font-family: {AppConfig.FONT_FAMILY};
                font-size: {AppConfig.FONT_SIZE_NORMAL}pt;
            }}
            QLabel {{
                color: {AppConfig.TEXT_COLOR};
            }}
            QLineEdit, QComboBox {{
                background-color: #3f5161;
                border: 1px solid {AppConfig.PRIMARY_COLOR};
                border-radius: 5px;
                padding: 5px;
                color: {AppConfig.TEXT_COLOR};
            }}
            QComboBox::drop-down {{
                border: 0px;
            }}
            QComboBox::down-arrow {{
                image: url(assets/icons/chevron-down.png);
                width: 16px;
                height: 16px;
            }}
            QPushButton {{
                background-color: {AppConfig.PRIMARY_COLOR};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 8px 15px;
                font-size: {AppConfig.FONT_SIZE_NORMAL}pt;
            }}
            QPushButton:hover {{
                background-color: {AppConfig.SECONDARY_COLOR};
            }}
            QTableWidget {{
                background-color: #2c3e50;
                color: {AppConfig.TEXT_COLOR};
                border: 1px solid {AppConfig.PRIMARY_COLOR};
                gridline-color: #555;
            }}
            QHeaderView::section {{
                background-color: {AppConfig.PRIMARY_COLOR};
                color: white;
                padding: 5px;
                border: 1px solid #555;
            }}
            QTableWidget::item {{
                padding: 5px;
            }}
            #cartTotalLabel {{
                font-size: {AppConfig.FONT_SIZE_LARGE}pt;
                font-weight: bold;
                color: {AppConfig.SECONDARY_COLOR};
            }}
        """)
        self.init_ui()
        self.load_categories()
        self.load_products_to_table()

    def init_ui(self):
        main_layout = QHBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)

        # Left side: Product List and Filters
        left_panel = QVBoxLayout()

        # Filters
        filter_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search product name or brand...")
        self.search_input.textChanged.connect(self.load_products_to_table)
        filter_layout.addWidget(QLabel("Search:"))
        filter_layout.addWidget(self.search_input)

        self.category_filter_combo = QComboBox()
        self.category_filter_combo.addItem("All Categories", None)
        self.category_filter_combo.currentIndexChanged.connect(self.load_products_to_table)
        filter_layout.addWidget(QLabel("Category:"))
        filter_layout.addWidget(self.category_filter_combo)
        filter_layout.addStretch()
        left_panel.addLayout(filter_layout)

        # Product Table
        self.product_table = QTableWidget()
        self.product_table.setColumnCount(5)  # Name, Brand, Price, Stock, Add to Cart
        self.product_table.setHorizontalHeaderLabels(["Product Name", "Brand", "Price", "Stock", "Action"])
        self.product_table.horizontalHeader().setStretchLastSection(True)
        self.product_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.product_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        left_panel.addWidget(self.product_table)

        main_layout.addLayout(left_panel, 2)  # 2/3 width

        # Right side: Cart and Checkout
        right_panel = QVBoxLayout()
        right_panel.setAlignment(Qt.AlignmentFlag.AlignTop)

        cart_label = QLabel("Shopping Cart")
        cart_label.setFont(QFont(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_LARGE, QFont.Weight.Bold))
        cart_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        right_panel.addWidget(cart_label)

        self.cart_table = QTableWidget()
        self.cart_table.setColumnCount(6)  # Product, Quantity, Price, Subtotal, Edit, Remove
        self.cart_table.setHorizontalHeaderLabels(["Product", "Qty", "Price", "Subtotal", "Edit", "Remove"])
        self.cart_table.horizontalHeader().setStretchLastSection(False)
        self.cart_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        right_panel.addWidget(self.cart_table)

        self.total_label = QLabel("Total: $0.00")
        self.total_label.setObjectName("cartTotalLabel")
        self.total_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        right_panel.addWidget(self.total_label)

        checkout_button = QPushButton("Checkout")
        checkout_button.setIcon(get_feather_icon("shopping-cart", size=16))
        checkout_button.clicked.connect(self.process_checkout)
        right_panel.addWidget(checkout_button)

        main_layout.addLayout(right_panel, 1)  # 1/3 width

    def load_categories(self):
        categories = self.product_manager.get_categories()
        self.category_filter_combo.clear()
        self.category_filter_combo.addItem("All Categories", None)
        for cat in categories:
            self.category_filter_combo.addItem(cat['name'], cat['id'])

    def load_products_to_table(self):
        search_term = self.search_input.text().strip()
        category_id = self.category_filter_combo.currentData()

        # Limit the number of products to prevent stack overflow
        products = self.product_manager.get_products(category_id=category_id, search_term=search_term)[:100]  # Limit to 100 products
        self.product_table.setRowCount(len(products))
        
        # Set larger row heights for better readability
        self.product_table.verticalHeader().setDefaultSectionSize(50)  # Increase row height
        
        # Make header text larger
        header_font = self.product_table.horizontalHeader().font()
        header_font.setPointSize(12)  # Larger font
        self.product_table.horizontalHeader().setFont(header_font)
        
        # Create a base font for all table items
        base_font = self.product_table.font()
        base_font.setPointSize(12)  # Larger font
        
        for row, product in enumerate(products):
            # Create items with larger font
            name_item = QTableWidgetItem(product['name'])
            brand_item = QTableWidgetItem(product.get('brand', 'N/A'))
            price_item = QTableWidgetItem(f"${product['price']:.2f}")
            stock_item = QTableWidgetItem(str(product['stock']))
            
            # Set font for all items
            name_item.setFont(base_font)
            brand_item.setFont(base_font)
            price_item.setFont(base_font)
            stock_item.setFont(base_font)
            
            self.product_table.setItem(row, 0, name_item)
            self.product_table.setItem(row, 1, brand_item)
            self.product_table.setItem(row, 2, price_item)
            self.product_table.setItem(row, 3, stock_item)

            add_to_cart_btn = QPushButton("Add to Cart")
            add_to_cart_btn.setMinimumHeight(30)  # Taller button
            add_to_cart_btn.setIcon(get_feather_icon("plus-circle", size=16))
            add_to_cart_btn.clicked.connect(lambda _, p=product: self.add_to_cart(p))

            # Disable if out of stock
            if product['stock'] <= 0:
                add_to_cart_btn.setEnabled(False)
                add_to_cart_btn.setText("Out of Stock")
                add_to_cart_btn.setStyleSheet("background-color: #c0392b; color: white;")  # Red for out of stock

            self.product_table.setCellWidget(row, 4, add_to_cart_btn)
        
        # Set minimum column widths to ensure visibility
        min_width = {
            0: 200,   # Product name
            1: 150,   # Brand
            2: 100,   # Price
            3: 80,    # Stock
            4: 120    # Action button
        }
        
        for col, width in min_width.items():
            self.product_table.setColumnWidth(col, width)

    def add_to_cart(self, product):
        product_id = product['id']
        current_stock = product['stock']
        
        if current_stock <= 0:
            QMessageBox.warning(self, "Out of Stock", f"{product['name']} is out of stock.")
            return
        
        # Show a quantity selection dialog
        from PyQt6.QtWidgets import QInputDialog
        quantity, ok = QInputDialog.getInt(
            self, 
            "Select Quantity", 
            f"How many {product['name']} would you like to add to cart?",
            value=1, 
            min=1, 
            max=current_stock
        )
        
        if not ok:
            return  # User canceled the dialog
        
        # Check if the product is already in cart
        if product_id in self.cart:
            current_cart_qty = self.cart[product_id]['quantity']
            if current_cart_qty + quantity > current_stock:
                QMessageBox.warning(
                    self, 
                    "Limit Reached", 
                    f"Cannot add {quantity} more of {product['name']}. Maximum available is {current_stock - current_cart_qty}."
                )
                return
            self.cart[product_id]['quantity'] += quantity
            QMessageBox.information(self, "Added to Cart", f"Added {quantity} more {product['name']} to your cart.")
        else:
            self.cart[product_id] = {'product_data': product, 'quantity': quantity}
            QMessageBox.information(self, "Added to Cart", f"Added {quantity} {product['name']} to your cart.")
            
        self.update_cart_display()

    def update_cart_display(self):
        self.cart_table.setRowCount(0)  # Clear table
        total_price = 0.0
        row = 0
        
        # Set larger row heights for better readability
        self.cart_table.verticalHeader().setDefaultSectionSize(50)  # Increase row height
        
        # Make header text larger
        header_font = self.cart_table.horizontalHeader().font()
        header_font.setPointSize(12)  # Larger font
        self.cart_table.horizontalHeader().setFont(header_font)
        
        # Create a base font for all table items
        base_font = self.cart_table.font()
        base_font.setPointSize(12)  # Larger font
        
        for product_id, item in self.cart.items():
            product = item['product_data']
            quantity = item['quantity']
            # Convert price to float if it's a Decimal
            price = float(product['price'])
            subtotal = price * quantity
            total_price += subtotal

            self.cart_table.insertRow(row)
            
            # Create table items with larger font
            name_item = QTableWidgetItem(product['name'])
            qty_item = QTableWidgetItem(str(quantity))
            price_item = QTableWidgetItem(f"${price:.2f}")
            subtotal_item = QTableWidgetItem(f"${subtotal:.2f}")
            
            # Set font for all items
            name_item.setFont(base_font)
            qty_item.setFont(base_font)
            price_item.setFont(base_font)
            subtotal_item.setFont(base_font)
            
            self.cart_table.setItem(row, 0, name_item)
            self.cart_table.setItem(row, 1, qty_item)
            self.cart_table.setItem(row, 2, price_item)
            self.cart_table.setItem(row, 3, subtotal_item)
            
            # Edit quantity button
            edit_btn = QPushButton()
            edit_btn.setMinimumHeight(30)  # Taller button
            edit_btn.setIcon(get_feather_icon("edit-2", size=16))
            edit_btn.setToolTip("Edit Quantity")
            edit_btn.clicked.connect(lambda _, p_id=product_id: self.edit_cart_quantity(p_id))
            
            # Remove button
            remove_btn = QPushButton()
            remove_btn.setMinimumHeight(30)  # Taller button
            remove_btn.setIcon(get_feather_icon("trash-2", size=16))
            remove_btn.setToolTip("Remove from Cart")
            remove_btn.clicked.connect(lambda _, p_id=product_id: self.remove_from_cart(p_id))
            
            # Add buttons to table
            self.cart_table.setCellWidget(row, 4, edit_btn)
            self.cart_table.setCellWidget(row, 5, remove_btn)
            
            row += 1

        self.total_label.setText(f"Total: ${total_price:.2f}")
        
        # Set column widths
        self.cart_table.setColumnWidth(0, 180)  # Product name
        self.cart_table.setColumnWidth(1, 60)   # Quantity
        self.cart_table.setColumnWidth(2, 80)   # Price
        self.cart_table.setColumnWidth(3, 100)  # Subtotal
        self.cart_table.setColumnWidth(4, 50)   # Edit button
        self.cart_table.setColumnWidth(5, 50)   # Remove button

    def edit_cart_quantity(self, product_id):
        """Allow the user to edit the quantity of a product in the cart"""
        if product_id not in self.cart:
            return
            
        product = self.cart[product_id]['product_data']
        current_qty = self.cart[product_id]['quantity']
        available_stock = product['stock']
        
        from PyQt6.QtWidgets import QInputDialog
        new_qty, ok = QInputDialog.getInt(
            self, 
            "Update Quantity", 
            f"Enter new quantity for {product['name']}:",
            value=current_qty,
            min=1,
            max=available_stock
        )
        
        if ok and new_qty != current_qty:
            self.cart[product_id]['quantity'] = new_qty
            QMessageBox.information(
                self, 
                "Cart Updated", 
                f"Updated {product['name']} quantity to {new_qty}"
            )
            self.update_cart_display()

    def remove_from_cart(self, product_id):
        """Remove a product from the cart"""
        if product_id not in self.cart:
            return
            
        product_name = self.cart[product_id]['product_data']['name']
        
        reply = QMessageBox.question(
            self,
            "Remove Item",
            f"Remove {product_name} from your cart?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        
        if reply == QMessageBox.StandardButton.Yes:
            del self.cart[product_id]
            self.update_cart_display()
            QMessageBox.information(self, "Item Removed", f"{product_name} removed from cart")

    def process_checkout(self):
        if not self.cart:
            QMessageBox.warning(self, "Cart Empty", "Your cart is empty. Please add items before checking out.")
            return

        confirm_dialog = QMessageBox()
        confirm_dialog.setIcon(QMessageBox.Icon.Question)
        confirm_dialog.setText(f"Confirm purchase of items totaling: {self.total_label.text()}?")
        confirm_dialog.setWindowTitle("Confirm Checkout")
        confirm_dialog.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        confirm_dialog.setDefaultButton(QMessageBox.StandardButton.Yes)
        confirm_dialog.setStyleSheet(f"""
            QMessageBox {{
                background-color: {AppConfig.BACKGROUND_COLOR};
                color: {AppConfig.TEXT_COLOR};
            }}
            QMessageBox QLabel {{
                color: {AppConfig.TEXT_COLOR};
            }}
            QPushButton {{
                background-color: {AppConfig.PRIMARY_COLOR};
                color: white;
                border: none;
                border-radius: 5px;
                padding: 5px 10px;
            }}
            QPushButton:hover {{
                background-color: {AppConfig.SECONDARY_COLOR};
            }}
        """)

        if confirm_dialog.exec() == QMessageBox.StandardButton.Yes:
            success_count = 0
            for product_id, item in self.cart.items():
                product = item['product_data']
                quantity = item['quantity']
                total_price = product['price'] * quantity

                if self.sales_manager.record_sale(product_id, quantity, total_price, self.current_user['id']):
                    success_count += 1
                    
                    # Log the sale
                    self.activity_logger.log_activity(
                        user_info=self.current_user,
                        action="PRODUCT_SALE",
                        target=product['name'],
                        details={
                            "product_id": product_id,
                            "quantity": quantity,
                            "total_price": float(total_price)
                        }
                    )
                else:
                    QMessageBox.warning(self, "Sale Error", f"Failed to record sale for {product['name']}.")

            if success_count == len(self.cart):
                QMessageBox.information(self, "Checkout Successful", "All items checked out successfully!")
                self.cart.clear()
                self.update_cart_display()
                self.load_products_to_table()  # Refresh product list to show updated stock
            else:
                QMessageBox.critical(self, "Checkout Incomplete",
                                     "Some items could not be processed. Please check logs.")




# =============================================================================
# SHARED: BadgeLabel - Reusable for Role, Status, Stock Level, etc.
# =============================================================================
class BadgeLabel(QLabel):
    """Reusable colored badge for roles, status, stock levels, etc."""
    def __init__(self, text: str, badge_type: str):
        super().__init__(text)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setFixedHeight(28)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)

        # Color mapping (consistent across entire app)
        styles = {
            # Roles
            "Admin": ("#ffebee", "#c62828"),       # Light red / dark red
            "Manager": ("#e3f2fd", "#1565c0"),     # Light blue / dark blue
            "Retailer": ("#e8f5e9", "#2e7d32"),    # Light green / dark green

            # Status
            "Active": ("#e8f5e9", "#2e7d32"),
            "Suspended": ("#fff8e1", "#f9a825"),
            "Inactive": ("#ffebee", "#c62828"),

            # Stock Status
            "In Stock": ("#e8f5e9", "#2e7d32"),
            "Low Stock": ("#fff3e0", "#ef6c00"),
            "No Stock": ("#ffebee", "#c62828"),
        }

        bg, fg = styles.get(badge_type, ("#f5f5f5", "#333333"))
        self.setStyleSheet(f"""
            QLabel {{
                background-color: {bg};
                color: {fg};
                border-radius: 14px;
                padding: 4px 12px;
                font-weight: bold;
                font-size: {AppConfig.FONT_SIZE_NORMAL - 1}pt;
                min-width: 70px;
            }}
        """)


# =============================================================================
# ProductCardWidget - Used in Manager Dashboard & Product Management
# =============================================================================
class ProductCardWidget(QFrame):
    """Modern product card with image, details, and role-based actions"""
    editClicked = pyqtSignal(int)
    addStockClicked = pyqtSignal(int)

    def __init__(self, product_data: dict, current_user: dict, parent=None):
        super().__init__(parent)
        self.product_data = product_data
        self.current_user = current_user
        self.product_manager = ProductManager()
        self.activity_logger = ActivityLogger()

        self.setObjectName("productCard")
        self.setStyleSheet(get_product_card_style())
        self.setFixedSize(260, 480)
        self.setCursor(Qt.CursorShape.PointingHandCursor)

        self.init_ui()
        self.update_visibility()

    def init_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Image
        self.image_label = QLabel()
        self.image_label.setFixedSize(230, 230)
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setScaledContents(True)
        self.image_label.setStyleSheet("""
            QLabel { border: 2px solid #e0e0e0; border-radius: 12px; background: #fafafa; }
        """)
        self.update_image()
        layout.addWidget(self.image_label, alignment=Qt.AlignmentFlag.AlignCenter)

        # Info Container
        info = QVBoxLayout()
        info.setSpacing(6)

        # Name
        name = QLabel(self.product_data.get("name", "Unknown Product"))
        name.setProperty("class", "product-title")
        name.setWordWrap(True)
        name.setAlignment(Qt.AlignmentFlag.AlignCenter)
        name.setFont(QFont(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_MEDIUM, QFont.Weight.Bold))
        info.addWidget(name)

        # Brand
        brand = QLabel(f"Brand: {self.product_data.get('brand', 'N/A')}")
        brand.setProperty("class", "product-detail")
        brand.setAlignment(Qt.AlignmentFlag.AlignCenter)
        info.addWidget(brand)

        # Price
        price = float(self.product_data.get("price", 0))
        price_label = QLabel(f"${price:.2f}")
        price_label.setProperty("class", "product-price")
        price_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        price_label.setFont(QFont(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_LARGE, QFont.Weight.Bold))
        price_label.setStyleSheet(f"color: {AppConfig.PRIMARY_BLUE};")
        info.addWidget(price_label)

        # Stock Status Badge
        stock = self.product_data.get("stock", 0)
        min_stock = self.product_data.get("min_stock_level", 5)
        if stock <= 0:
            status = "No Stock"
        elif stock <= min_stock:
            status = "Low Stock"
        else:
            status = "In Stock"

        self.stock_badge = BadgeLabel(f"{stock} ({status})", status)
        info.addWidget(self.stock_badge, alignment=Qt.AlignmentFlag.AlignCenter)

        # Category
        cat = QLabel(f"Category: {self.product_data.get('category', 'Uncategorized')}")
        cat.setAlignment(Qt.AlignmentFlag.AlignCenter)
        cat.setStyleSheet("color: #666; font-size: 11pt;")
        info.addWidget(cat)

        layout.addLayout(info)

        # Action Buttons
        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(10)

        self.add_stock_btn = QPushButton("Add Stock")
        self.add_stock_btn.setIcon(get_feather_icon("plus-square"))
        self.add_stock_btn.clicked.connect(lambda: self.addStockClicked.emit(self.product_data["id"]))

        self.edit_btn = QPushButton("Edit")
        self.edit_btn.setIcon(get_feather_icon("edit"))
        self.edit_btn.clicked.connect(lambda: self.editClicked.emit(self.product_data["id"]))

        btn_layout.addWidget(self.add_stock_btn)
        btn_layout.addWidget(self.edit_btn)
        layout.addLayout(btn_layout)

    def update_image(self):
        path = self.product_data.get("image_path")
        pixmap = load_product_image(path, target_size=(230, 230), keep_aspect_ratio=True)
        if pixmap.isNull():
            pixmap = QPixmap(230, 230)
            pixmap.fill(Qt.GlobalColor.lightGray)
        self.image_label.setPixmap(pixmap)

    def update_visibility(self):
        role = self.current_user.get("role", "").lower()
        is_retailer = role == "retailer"
        self.add_stock_btn.setVisible(not is_retailer)
        self.edit_btn.setVisible(not is_retailer)

    def update_card_data(self, new_data: dict):
        self.product_data.update(new_data)
        self.findChild(QLabel, "", Qt.FindChildOption.FindChildrenRecursively)
        for label in self.findChildren(QLabel):
            text = label.text()
            if "Brand:" in text:
                label.setText(f"Brand: {new_data.get('brand', 'N/A')}")
            elif label.property("class") == "product-title":
                label.setText(new_data.get("name", "Unknown"))
            elif "Category:" in text:
                label.setText(f"Category: {new_data.get('category', 'Uncategorized')}")
            elif "$" in text and "price" in label.property("class"):
                label.setText(f"${float(new_data.get('price', 0)):.2f}")

        self.update_image()
        stock = new_data.get("stock", 0)
        min_stock = new_data.get("min_stock_level", 5)
        status = "No Stock" if stock <= 0 else "Low Stock" if stock <= min_stock else "In Stock"
        self.stock_badge.setText(f"{stock} ({status})")
        self.stock_badge.badge_type = status  # For future styling if needed
        self.update_visibility()


# =============================================================================
# Optional: LowStockTableWidget, ExpiringItemsWidget (for Manager Dashboard)
# =============================================================================
class LowStockTableWidget(QTableWidget):
    def __init__(self, parent=None):
        super().__init__(0, 5, parent)
        self.setHorizontalHeaderLabels(["Product", "Brand", "Current Stock", "Min Level", "Status"])
        apply_table_styles(self)
        self.horizontalHeader().setStretchLastSection(True)
        self.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

    def load_data(self, products):
        self.setRowCount(0)
        for prod in products:
            if prod["stock"] > prod.get("min_stock_level", 5):
                continue
            row = self.rowCount()
            self.insertRow(row)
            self.setItem(row, 0, QTableWidgetItem(prod["name"]))
            self.setItem(row, 1, QTableWidgetItem(prod.get("brand", "N/A")))
            self.setItem(row, 2, QTableWidgetItem(str(prod["stock"])))
            self.setItem(row, 3, QTableWidgetItem(str(prod.get("min_stock_level", 5))))
            status = BadgeLabel("Low Stock" if prod["stock"] > 0 else "No Stock", "Low Stock" if prod["stock"] > 0 else "No Stock")
            self.setCellWidget(row, 4, status)


# =============================================================================
# Export for use in other modules
# =============================================================================
__all__ = [
    "BadgeLabel",
    "ProductCardWidget",
    "LowStockTableWidget",
    "apply_table_styles",
    "get_product_card_style"
]