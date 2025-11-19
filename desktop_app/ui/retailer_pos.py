"""
Retailer Point of Sale (POS) with Gamification
Features: Product search, cart management, checkout, streak tracking, achievements
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QTableWidget, QTableWidgetItem, QFrame, QHeaderView, QDialog,
    QScrollArea, QMessageBox, QSpinBox
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from api_client.stockadoodle_api import StockaDoodleAPI
from utils.config import AppConfig
from utils.decorators import role_required
from utils.helpers import get_feather_icon
from utils.styles import apply_table_styles


class RetailerPOSWidget(QWidget):
    """Retailer Point of Sale Interface with Gamification"""
    
    def __init__(self, api_client: StockaDoodleAPI, current_user: dict, parent=None):
        super().__init__(parent)
        self.api = api_client
        self.current_user = current_user
        
        # Cart state
        self.cart_items = []  # [{product_id, name, price, quantity}]
        
        # Gamification state
        self.current_streak = 0
        self.daily_quota = 0.0
        self.sales_today = 0.0
        self.achievements = []
        
        self.setStyleSheet(f"background-color: {AppConfig.BACKGROUND_COLOR};")
        self.init_ui()
        
        # Load data
        QTimer.singleShot(100, self.load_initial_data)
        
    def init_ui(self):
        """Initialize the UI layout"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)
        
        # Gamification Header
        gamification_header = self._create_gamification_header()
        main_layout.addWidget(gamification_header)
        
        # Split Layout: Products (65%) + Cart (35%)
        split_layout = QHBoxLayout()
        split_layout.setSpacing(20)
        
        # Left: Product Catalog
        product_section = self._create_product_section()
        split_layout.addWidget(product_section, 65)
        
        # Right: Shopping Cart
        cart_section = self._create_cart_section()
        split_layout.addWidget(cart_section, 35)
        
        main_layout.addLayout(split_layout)
        
    def _create_gamification_header(self) -> QFrame:
        """Create the gamification metrics header"""
        header = QFrame()
        header.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 {AppConfig.PRIMARY_COLOR}, stop:1 {AppConfig.SECONDARY_COLOR});
                border-radius: 10px;
                padding: 15px;
            }}
        """)
        
        layout = QHBoxLayout(header)
        layout.setContentsMargins(15, 10, 15, 10)
        
        # Streak Display
        self.streak_label = QLabel("🔥 0 Day Streak")
        self.streak_label.setStyleSheet("color: white; font-size: 16pt; font-weight: bold;")
        layout.addWidget(self.streak_label)
        
        layout.addSpacing(30)
        
        # Quota Display
        self.quota_label = QLabel("💰 Sales: $0.00 / Quota: $0.00")
        self.quota_label.setStyleSheet("color: white; font-size: 16pt; font-weight: bold;")
        layout.addWidget(self.quota_label)
        
        layout.addStretch()
        
        # Achievements Button
        self.achievements_btn = QPushButton("🏆 Achievements")
        self.achievements_btn.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: #6C5CE7;
                padding: 10px 20px;
                border-radius: 8px;
                font-weight: bold;
                font-size: 11pt;
            }
            QPushButton:hover {
                background-color: #f0f0f0;
            }
        """)
        self.achievements_btn.clicked.connect(self.show_achievements_dialog)
        layout.addWidget(self.achievements_btn)
        
        return header
        
    def _create_product_section(self) -> QFrame:
        """Create the product browsing section"""
        section = QFrame()
        section.setStyleSheet(f"""
            QFrame {{
                background-color: {AppConfig.CARD_BACKGROUND};
                border-radius: 12px;
                padding: 15px;
            }}
        """)
        
        layout = QVBoxLayout(section)
        
        # Title
        title = QLabel("Product Catalog")
        title.setFont(QFont(AppConfig.FONT_FAMILY, 14, QFont.Weight.Bold))
        title.setStyleSheet("color: white; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Search Bar
        search_layout = QHBoxLayout()
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search products by name or ID...")
        self.search_input.textChanged.connect(self.filter_products)
        search_layout.addWidget(self.search_input)
        
        self.add_to_cart_btn = QPushButton("Add to Cart")
        self.add_to_cart_btn.setIcon(get_feather_icon("plus-circle", "white", 16))
        self.add_to_cart_btn.clicked.connect(self.add_selected_to_cart)
        self.add_to_cart_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {AppConfig.PRIMARY_COLOR};
                color: white;
                padding: 8px 15px;
                border-radius: 6px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {AppConfig.SECONDARY_COLOR};
            }}
        """)
        search_layout.addWidget(self.add_to_cart_btn)
        
        layout.addLayout(search_layout)
        
        # Products Table
        self.products_table = QTableWidget(0, 4)
        self.products_table.setHorizontalHeaderLabels(["ID", "Name", "Price", "Stock"])
        apply_table_styles(self.products_table)
        self.products_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        header = self.products_table.horizontalHeader()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.products_table)
        
        return section
        
    def _create_cart_section(self) -> QFrame:
        """Create the shopping cart section"""
        section = QFrame()
        section.setStyleSheet(f"""
            QFrame {{
                background-color: {AppConfig.CARD_BACKGROUND};
                border-radius: 12px;
                padding: 15px;
            }}
        """)
        
        layout = QVBoxLayout(section)
        
        # Title
        title = QLabel("Shopping Cart")
        title.setFont(QFont(AppConfig.FONT_FAMILY, 14, QFont.Weight.Bold))
        title.setStyleSheet("color: white; margin-bottom: 10px;")
        layout.addWidget(title)
        
        # Cart Table
        self.cart_table = QTableWidget(0, 4)
        self.cart_table.setHorizontalHeaderLabels(["Product", "Qty", "Price", "Subtotal"])
        apply_table_styles(self.cart_table)
        self.cart_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        
        header = self.cart_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        
        layout.addWidget(self.cart_table)
        
        # Total Display
        total_layout = QHBoxLayout()
        total_label = QLabel("TOTAL:")
        total_label.setFont(QFont(AppConfig.FONT_FAMILY, 12, QFont.Weight.Bold))
        total_label.setStyleSheet("color: white;")
        
        self.total_value_label = QLabel("$0.00")
        self.total_value_label.setFont(QFont(AppConfig.FONT_FAMILY, 18, QFont.Weight.ExtraBold))
        self.total_value_label.setStyleSheet(f"color: {AppConfig.SUCCESS_COLOR};")
        
        total_layout.addStretch()
        total_layout.addWidget(total_label)
        total_layout.addWidget(self.total_value_label)
        
        layout.addLayout(total_layout)
        
        # Checkout Button
        self.checkout_btn = QPushButton("Process Checkout")
        self.checkout_btn.setIcon(get_feather_icon("shopping-cart", "white", 16))
        self.checkout_btn.setMinimumHeight(50)
        self.checkout_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {AppConfig.SUCCESS_COLOR};
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 14pt;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: #00a080;
            }}
        """)
        self.checkout_btn.clicked.connect(self.process_checkout)
        layout.addWidget(self.checkout_btn)
        
        # Cart Actions
        actions_layout = QHBoxLayout()
        
        remove_btn = QPushButton("Remove Item")
        remove_btn.clicked.connect(self.remove_from_cart)
        remove_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {AppConfig.ERROR_COLOR};
                color: white;
                padding: 8px;
                border-radius: 6px;
            }}
        """)
        
        clear_btn = QPushButton("Clear Cart")
        clear_btn.clicked.connect(self.clear_cart)
        clear_btn.setStyleSheet("""
            QPushButton {
                background-color: #555;
                color: white;
                padding: 8px;
                border-radius: 6px;
            }
        """)
        
        actions_layout.addWidget(remove_btn)
        actions_layout.addWidget(clear_btn)
        
        layout.addLayout(actions_layout)
        
        return section
        
    def load_initial_data(self):
        """Load initial data: metrics and products"""
        self.load_retailer_metrics()
        self.load_products()
        
    def load_retailer_metrics(self):
        """Load gamification metrics from API"""
        user_id = self.current_user.get('id')
        if not user_id:
            return
            
        try:
            resp = self.api.retailer_metrics.get_metrics(user_id)
            
            if resp.success:
                data = resp.data
                self.current_streak = data.get('current_streak', 0)
                self.daily_quota = data.get('daily_quota_usd', 0.0)
                self.sales_today = data.get('daily_quota_usd', 0.0)  # Current day sales
                
                # Fetch achievements
                achievements = self.api.retailer_metrics.get_achievements(user_id)
                if isinstance(achievements, dict):
                    self.achievements = achievements.get('achievements', [])
                
                self._update_gamification_display()
                
        except Exception as e:
            print(f"Error loading retailer metrics: {e}")
            
    def _update_gamification_display(self):
        """Update the gamification header with current values"""
        self.streak_label.setText(f"🔥 {self.current_streak} Day Streak")
        self.quota_label.setText(
            f"💰 Sales: ${self.sales_today:,.2f} / Quota: ${self.daily_quota:,.2f}"
        )
        
        # Highlight if quota achieved
        if self.sales_today >= self.daily_quota and self.daily_quota > 0:
            self.quota_label.setStyleSheet(
                "color: #FFD700; font-size: 16pt; font-weight: bold;"
            )
        
    def load_products(self):
        """Load all available products"""
        try:
            resp = self.api.products.list()
            
            if resp.success:
                self.all_products = resp.data
                self.filter_products()
                
        except Exception as e:
            print(f"Error loading products: {e}")
            
    def filter_products(self):
        """Filter products based on search input"""
        search_text = self.search_input.text().lower()
        
        self.products_table.setRowCount(0)
        
        for product in self.all_products:
            # Filter logic
            if search_text and search_text not in product.get('name', '').lower():
                if search_text != str(product.get('id', '')):
                    continue
                    
            # Add to table
            row = self.products_table.rowCount()
            self.products_table.insertRow(row)
            
            self.products_table.setItem(row, 0, QTableWidgetItem(str(product['id'])))
            self.products_table.setItem(row, 1, QTableWidgetItem(product['name']))
            self.products_table.setItem(row, 2, QTableWidgetItem(f"${product['price']:.2f}"))
            self.products_table.setItem(row, 3, QTableWidgetItem(str(product.get('stock_level', 0))))
            
    def add_selected_to_cart(self):
        """Add the selected product to cart"""
        selected_rows = self.products_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select a product to add.")
            return
            
        row = selected_rows[0].row()
        product_id = int(self.products_table.item(row, 0).text())
        product_name = self.products_table.item(row, 1).text()
        price = float(self.products_table.item(row, 2).text().replace('$', ''))
        stock = int(self.products_table.item(row, 3).text())
        
        if stock <= 0:
            QMessageBox.warning(self, "Out of Stock", f"{product_name} is out of stock.")
            return
            
        # Check if already in cart
        for item in self.cart_items:
            if item['product_id'] == product_id:
                if item['quantity'] < stock:
                    item['quantity'] += 1
                    self.refresh_cart_display()
                    return
                else:
                    QMessageBox.warning(self, "Stock Limit", "Maximum stock reached in cart.")
                    return
                    
        # Add new item
        self.cart_items.append({
            'product_id': product_id,
            'name': product_name,
            'price': price,
            'quantity': 1
        })
        
        self.refresh_cart_display()
        
    def remove_from_cart(self):
        """Remove selected item from cart"""
        selected_rows = self.cart_table.selectionModel().selectedRows()
        if not selected_rows:
            QMessageBox.warning(self, "No Selection", "Please select an item to remove.")
            return
            
        row = selected_rows[0].row()
        self.cart_items.pop(row)
        self.refresh_cart_display()
        
    def clear_cart(self):
        """Clear all items from cart"""
        self.cart_items = []
        self.refresh_cart_display()
        
    def refresh_cart_display(self):
        """Refresh the cart table and total"""
        self.cart_table.setRowCount(0)
        
        total = 0.0
        
        for item in self.cart_items:
            row = self.cart_table.rowCount()
            self.cart_table.insertRow(row)
            
            subtotal = item['price'] * item['quantity']
            total += subtotal
            
            self.cart_table.setItem(row, 0, QTableWidgetItem(item['name']))
            self.cart_table.setItem(row, 1, QTableWidgetItem(str(item['quantity'])))
            self.cart_table.setItem(row, 2, QTableWidgetItem(f"${item['price']:.2f}"))
            self.cart_table.setItem(row, 3, QTableWidgetItem(f"${subtotal:.2f}"))
            
        self.total_value_label.setText(f"${total:,.2f}")
        
    @role_required('Retailer')
    def process_checkout(self):
        """Process the checkout and record sale"""
        if not self.cart_items:
            QMessageBox.warning(self, "Empty Cart", "Please add items to cart first.")
            return
            
        total = sum(item['price'] * item['quantity'] for item in self.cart_items)
        retailer_id = self.current_user.get('id')
        
        # Prepare items for API
        api_items = [
            {
                'product_id': item['product_id'],
                'quantity': item['quantity'],
                'price': item['price']
            }
            for item in self.cart_items
        ]
        
        try:
            resp = self.api.sales_enhanced.record(
                retailer_id=retailer_id,
                items=api_items,
                total_amount=total
            )
            
            if resp.success:
                QMessageBox.information(
                    self, "Success",
                    f"Sale of ${total:,.2f} recorded successfully!"
                )
                
                # Refresh metrics and clear cart
                self.load_retailer_metrics()
                self.load_products()  # Refresh stock levels
                self.clear_cart()
            else:
                QMessageBox.critical(self, "Error", f"Failed to process sale: {resp.error}")
                
        except Exception as e:
            QMessageBox.critical(self, "Error", f"Checkout failed: {str(e)}")
            
    def show_achievements_dialog(self):
        """Show achievements in a modal dialog"""
        dialog = QDialog(self)
        dialog.setWindowTitle("🏆 Your Achievements")
        dialog.setFixedSize(500, 600)
        dialog.setStyleSheet(f"background-color: {AppConfig.BACKGROUND_COLOR}; color: white;")
        
        layout = QVBoxLayout(dialog)
        
        title = QLabel("Retailer Milestones")
        title.setFont(QFont(AppConfig.FONT_FAMILY, 18, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {AppConfig.PRIMARY_COLOR}; margin-bottom: 15px;")
        layout.addWidget(title)
        
        # Scroll area for achievements
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none;")
        
        content = QWidget()
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(15)
        
        if not self.achievements:
            no_ach = QLabel("No achievements unlocked yet. Keep selling!")
            no_ach.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_ach.setStyleSheet("color: #888; font-size: 12pt;")
            content_layout.addWidget(no_ach)
        else:
            for achievement in self.achievements:
                ach_frame = QFrame()
                ach_frame.setStyleSheet(f"""
                    QFrame {{
                        background-color: {AppConfig.CARD_BACKGROUND};
                        border: 1px solid #555;
                        border-radius: 8px;
                        padding: 15px;
                    }}
                """)
                
                ach_layout = QVBoxLayout(ach_frame)
                
                name = QLabel(f"🌟 {achievement.get('name', 'Achievement')}")
                name.setFont(QFont(AppConfig.FONT_FAMILY, 12, QFont.Weight.Bold))
                name.setStyleSheet("color: #FFD700;")
                ach_layout.addWidget(name)
                
                desc = QLabel(achievement.get('description', ''))
                desc.setWordWrap(True)
                desc.setStyleSheet("color: #ccc;")
                ach_layout.addWidget(desc)
                
                content_layout.addWidget(ach_frame)
                
        content_layout.addStretch()
        scroll.setWidget(content)
        layout.addWidget(scroll)
        
        close_btn = QPushButton("Close")
        close_btn.clicked.connect(dialog.close)
        layout.addWidget(close_btn)
        
        dialog.exec()