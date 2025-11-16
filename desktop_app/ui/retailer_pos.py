from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QLineEdit, 
    QPushButton, QTableWidget, QHeaderView, QAbstractItemView, QTableWidgetItem, 
    QMessageBox, QDialog, QScrollArea
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor

from utils.config import AppConfig, CURRENT_SESSION
from utils.decorators import role_required
from utils.style_utils import setup_standard_table # Assuming this function exists

class RetailerDashboardWidget(QWidget):
    """
    Dashboard for Retailers: Point-of-Sale (POS) interface with Gamification metrics.
    """
    
    def __init__(self, api_client, current_user, parent=None):
        super().__init__(parent)
        self.api = api_client
        self.current_user = current_user
        
        # NEW: Gamification state
        self.current_streak = 0
        self.daily_quota = 0.0
        self.sales_today = 0.0 # Track sales for quota display
        self.achievements = []
        
        self.cart_items = []
        self.all_products = [] # Cached product list

        self.init_ui()
        QTimer.singleShot(10, self.load_retailer_metrics)
        QTimer.singleShot(10, self.load_products)
        
    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # 1. NEW: Gamification Header
        self.gamification_header = self._create_gamification_header()
        main_layout.addWidget(self.gamification_header)

        # 2. Main POS Interface (Horizontal Split)
        pos_layout = QHBoxLayout()
        pos_layout.setSpacing(20)

        # Left Side: Product Browsing (60%)
        product_section = self._create_product_browsing()
        pos_layout.addWidget(product_section, 60)

        # Right Side: Cart and Checkout (40%)
        cart_section = self._create_cart_checkout()
        pos_layout.addWidget(cart_section, 40)
        
        main_layout.addLayout(pos_layout)
        main_layout.addStretch(1)

    # --- Gamification Methods ---

    def _create_gamification_header(self):
        """NEW: Display streak and daily quota"""
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {AppConfig.COLOR_PURPLE}, stop:1 {AppConfig.COLOR_GREEN});
                border-radius: 10px;
                padding: 15px;
            }}
        """)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(10, 5, 10, 5)
        
        # Streak display
        self.streak_label = QLabel(f"🔥 0 Day Streak")
        self.streak_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        layout.addWidget(self.streak_label)
        
        layout.addSpacing(30)
        
        # Daily quota display
        self.quota_label = QLabel(f"💰 Quota: ${self.daily_quota:.2f} / Sales: ${self.sales_today:.2f}")
        self.quota_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")
        layout.addWidget(self.quota_label)
        
        layout.addStretch(1)
        
        # Achievements button
        self.achievements_btn = QPushButton("🏆 Achievements")
        self.achievements_btn.clicked.connect(self.show_achievements)
        self.achievements_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: white;
                color: {AppConfig.COLOR_PURPLE};
                padding: 8px 15px;
                border-radius: 8px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #f0f0f0;
            }}
        """)
        layout.addWidget(self.achievements_btn)
        
        return header

    def load_retailer_metrics(self):
        """NEW: Fetch gamification data from API"""
        user_id = self.current_user.get('id')
        if not user_id: return
        
        resp = self.api.metrics.get_retailer_metrics(user_id)
        if resp.success:
            data = resp.data
            self.current_streak = data.get('current_streak', 0)
            self.daily_quota = data.get('daily_quota_usd', 0.0)
            self.sales_today = data.get('sales_today_usd', 0.0)
            self.achievements = data.get('achievements', [])
            self._update_gamification_display()
        else:
            print(f"Failed to load metrics: {resp.message}")

    def _update_gamification_display(self):
        """Updates the labels in the header with current metric values."""
        self.streak_label.setText(f"🔥 {self.current_streak} Day Streak")
        self.quota_label.setText(f"💰 Quota: ${self.daily_quota:,.2f} / Sales: ${self.sales_today:,.2f}")
        
        # Style the quota label if achieved
        if self.sales_today >= self.daily_quota:
             self.quota_label.setStyleSheet("color: #FFD700; font-size: 18px; font-weight: bold;") # Gold
        else:
            self.quota_label.setStyleSheet("color: white; font-size: 18px; font-weight: bold;")

    def show_achievements(self):
        """Displays the retailer's achievements in a modal dialog."""
        dialog = QDialog(self)
        dialog.setWindowTitle("🏆 Retailer Achievements")
        dialog.setFixedSize(450, 600)
        dialog.setStyleSheet(f"background-color: {AppConfig.DARK_BG_COLOR}; color: white;")
        
        main_layout = QVBoxLayout(dialog)
        
        title = QLabel("Your Milestones")
        title.setFont(QFont(AppConfig.FONT_FAMILY, 16, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {AppConfig.ACCENT_COLOR}; margin-bottom: 10px;")
        main_layout.addWidget(title)
        
        # Scroll Area for Achievements
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        
        content_widget = QWidget()
        content_layout = QVBoxLayout(content_widget)
        content_layout.setSpacing(15)
        
        if not self.achievements:
            content_layout.addWidget(QLabel("No achievements unlocked yet. Start selling!"))
        
        for achievement in self.achievements:
            ach_frame = QFrame()
            ach_frame.setStyleSheet("""
                QFrame {
                    background-color: #333333;
                    border: 1px solid #555555;
                    border-radius: 8px;
                    padding: 10px;
                }
            """)
            ach_layout = QVBoxLayout(ach_frame)
            
            name_label = QLabel(f"🌟 {achievement.get('name', 'N/A')}")
            name_label.setFont(QFont(AppConfig.FONT_FAMILY, 12, QFont.Weight.Bold))
            name_label.setStyleSheet("color: #FFD700;") # Gold
            
            desc_label = QLabel(achievement.get('description', ''))
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("color: #D0D0D0;")
            
            date_label = QLabel(f"Unlocked: {achievement.get('unlocked_at', 'N/A')[:10]}")
            date_label.setStyleSheet("color: #888888; font-size: 9pt;")
            
            ach_layout.addWidget(name_label)
            ach_layout.addWidget(desc_label)
            ach_layout.addWidget(date_label)
            
            content_layout.addWidget(ach_frame)
            
        content_layout.addStretch(1)
        scroll.setWidget(content_widget)
        main_layout.addWidget(scroll)
        
        dialog.exec()
        
    # --- POS Interface Methods (Adapted from LogiJex) ---
    
    def _create_product_browsing(self):
        """Creates the product search and selection interface (Left side)."""
        section = QFrame()
        section.setStyleSheet(f"background-color: {AppConfig.DARK_SECONDARY_COLOR}; border-radius: 10px; padding: 15px;")
        layout = QVBoxLayout(section)
        
        title = QLabel("Product Search & Inventory")
        title.setFont(QFont(AppConfig.FONT_FAMILY, 14, QFont.Weight.Bold))
        title.setStyleSheet("color: white; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Search Bar
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search by product name or ID...")
        self.search_input.setStyleSheet(AppConfig.LINE_EDIT_STYLE)
        self.search_input.textChanged.connect(self.filter_products)
        
        self.add_to_cart_btn = QPushButton("Add to Cart")
        self.add_to_cart_btn.clicked.connect(self.add_selected_to_cart)
        self.add_to_cart_btn.setStyleSheet(AppConfig.BUTTON_PRIMARY_STYLE)
        self.add_to_cart_btn.setMinimumWidth(120)
        
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.add_to_cart_btn)
        layout.addLayout(search_layout)
        
        # Product Table
        self.product_table = QTableWidget(0, 4)
        self.product_table.setHorizontalHeaderLabels(["ID", "Name", "Price ($)", "Stock"])
        setup_standard_table(self.product_table)
        self.product_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.product_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.product_table)
        
        return section
        
    def _create_cart_checkout(self):
        """Creates the shopping cart and checkout interface (Right side)."""
        section = QFrame()
        section.setStyleSheet(f"background-color: {AppConfig.DARK_SECONDARY_COLOR}; border-radius: 10px; padding: 15px;")
        layout = QVBoxLayout(section)
        
        title = QLabel("Shopping Cart")
        title.setFont(QFont(AppConfig.FONT_FAMILY, 14, QFont.Weight.Bold))
        title.setStyleSheet("color: white; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Cart Table
        self.cart_table = QTableWidget(0, 4)
        self.cart_table.setHorizontalHeaderLabels(["Name", "Qty", "Price", "Subtotal"])
        setup_standard_table(self.cart_table)
        self.cart_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.cart_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        layout.addWidget(self.cart_table)
        
        # Total Display
        total_layout = QHBoxLayout()
        total_label = QLabel("TOTAL AMOUNT:")
        total_label.setFont(QFont(AppConfig.FONT_FAMILY, 12, QFont.Weight.Bold))
        total_label.setStyleSheet("color: white;")
        self.total_value_label = QLabel("$0.00")
        self.total_value_label.setFont(QFont(AppConfig.FONT_FAMILY, 14, QFont.Weight.ExtraBold))
        self.total_value_label.setStyleSheet(f"color: {AppConfig.ACCENT_COLOR};")
        
        total_layout.addStretch(1)
        total_layout.addWidget(total_label)
        total_layout.addWidget(self.total_value_label)
        layout.addLayout(total_layout)
        
        # Checkout Button
        self.checkout_btn = QPushButton("Process Checkout")
        self.checkout_btn.clicked.connect(self.process_checkout)
        self.checkout_btn.setStyleSheet(AppConfig.BUTTON_SUCCESS_STYLE)
        self.checkout_btn.setMinimumHeight(45)
        layout.addWidget(self.checkout_btn)
        
        # Clear/Remove Buttons
        action_layout = QHBoxLayout()
        remove_btn = QPushButton("Remove Item")
        remove_btn.clicked.connect(self.remove_from_cart)
        remove_btn.setStyleSheet(AppConfig.BUTTON_DANGER_STYLE)
        
        clear_btn = QPushButton("Clear Cart")
        clear_btn.clicked.connect(self.clear_cart)
        clear_btn.setStyleSheet(AppConfig.BUTTON_SECONDARY_STYLE)
        
        action_layout.addWidget(remove_btn)
        action_layout.addWidget(clear_btn)
        layout.addLayout(action_layout)
        
        return section
        
    def load_products(self):
        """Loads all active products from the API."""
        resp = self.api.products.list()
        if resp.success:
            self.all_products = resp.data
            self.filter_products()
        else:
            QMessageBox.warning(self, "API Error", f"Failed to load products: {resp.message}")

    def filter_products(self):
        """Filters the product list based on the search input and populates the table."""
        self.product_table.setRowCount(0)
        search_text = self.search_input.text().lower()
        
        filtered_products = [
            p for p in self.all_products 
            if search_text in p.get('name', '').lower() or search_text == str(p.get('id', 0))
        ]
        
        for row, product in enumerate(filtered_products):
            self.product_table.insertRow(row)
            self.product_table.setItem(row, 0, QTableWidgetItem(str(product['id'])))
            self.product_table.setItem(row, 1, QTableWidgetItem(product['name']))
            self.product_table.setItem(row, 2, QTableWidgetItem(f"{product['price']:.2f}"))
            self.product_table.setItem(row, 3, QTableWidgetItem(str(product['stock_level'])))
            
    def add_selected_to_cart(self):
        """Adds the currently selected product to the cart or increments quantity."""
        selected_rows = self.product_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Selection Error", "Please select a product to add.")
            return

        row = selected_rows[0].row()
        product_id = int(self.product_table.item(row, 0).text())
        product_name = self.product_table.item(row, 1).text()
        price = float(self.product_table.item(row, 2).text())
        stock = int(self.product_table.item(row, 3).text())

        if stock <= 0:
            QMessageBox.warning(self, "Stock Alert", f"'{product_name}' is out of stock.")
            return

        # Check if item is already in cart
        for item in self.cart_items:
            if item['product_id'] == product_id:
                if item['quantity'] < stock:
                    item['quantity'] += 1
                    item['subtotal'] = item['quantity'] * item['price']
                    self.refresh_cart()
                    return
                else:
                    QMessageBox.warning(self, "Stock Alert", f"Maximum stock for '{product_name}' reached in cart.")
                    return
        
        # Add new item to cart
        self.cart_items.append({
            'product_id': product_id,
            'name': product_name,
            'price': price,
            'quantity': 1,
            'subtotal': price
        })
        self.refresh_cart()
        
    def remove_from_cart(self):
        """Removes the selected item from the cart table."""
        selected_rows = self.cart_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "Selection Error", "Please select an item in the cart to remove.")
            return
            
        row = selected_rows[0].row()
        self.cart_items.pop(row)
        self.refresh_cart()

    def refresh_cart(self):
        """Repopulates the cart table and recalculates the total."""
        self.cart_table.setRowCount(0)
        total_amount = 0.0
        
        for row, item in enumerate(self.cart_items):
            self.cart_table.insertRow(row)
            self.cart_table.setItem(row, 0, QTableWidgetItem(item['name']))
            self.cart_table.setItem(row, 1, QTableWidgetItem(str(item['quantity'])))
            self.cart_table.setItem(row, 2, QTableWidgetItem(f"{item['price']:.2f}"))
            self.cart_table.setItem(row, 3, QTableWidgetItem(f"{item['subtotal']:.2f}"))
            total_amount += item['subtotal']
            
        self.total_value_label.setText(f"${total_amount:,.2f}")

    def clear_cart(self):
        """Clears all items from the cart."""
        self.cart_items = []
        self.refresh_cart()

    @role_required('Retailer')
    def process_checkout(self):
        """Modified: Submits the sale to the API, including retailer ID for gamification."""
        if not self.cart_items:
            QMessageBox.warning(self, "Checkout Error", "The cart is empty.")
            return

        total_amount = sum(item['subtotal'] for item in self.cart_items)
        retailer_id = self.current_user.get('id')
        
        # Prepare items for API: only ID, quantity, and subtotal
        api_items = [
            {'product_id': item['product_id'], 'quantity': item['quantity'], 'subtotal': item['subtotal']}
            for item in self.cart_items
        ]

        # NEW: Record sale with retailer_id for gamification and stock update
        resp = self.api.sales.record_sale(
            retailer_id=retailer_id,
            items=api_items,
            total_amount=total_amount
        )
        
        if resp.success:
            QMessageBox.information(self, "Success", f"Sale of ${total_amount:,.2f} recorded successfully!")
            self.load_retailer_metrics() # NEW: Refresh metrics after sale
            self.load_products() # Refresh stock levels
            self.clear_cart()
        else:
            QMessageBox.critical(self, "Checkout Failed", f"API Error: {resp.message}")