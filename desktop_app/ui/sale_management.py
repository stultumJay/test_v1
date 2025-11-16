from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
                             QMessageBox, QDialog, QFormLayout, QComboBox,
                             QDateEdit, QHeaderView)
from PyQt6.QtCore import Qt, QDate
from core.sales_manager import SalesManager
from core.product_manager import ProductManager  # To get product names for sales display
from core.activity_logger import ActivityLogger
from utils.helpers import get_feather_icon
from utils.config import AppConfig
from utils.decorators import role_required
from utils.styles import get_global_stylesheet, apply_table_styles


class SalesManagementWidget(QWidget):
    def __init__(self, current_user, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.sales_manager = SalesManager()
        self.product_manager = ProductManager()  # To fetch product details for display
        self.activity_logger = ActivityLogger()

        # Apply global style
        self.setStyleSheet(get_global_stylesheet())
        
        self.init_ui()
        self.load_sales_data()  # Initial load

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Date Filters
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Start Date:"))
        self.start_date_edit = QDateEdit(calendarPopup=True)
        self.start_date_edit.setDate(QDate.currentDate().addMonths(-1))  # Default to 1 month ago
        filter_layout.addWidget(self.start_date_edit)

        filter_layout.addWidget(QLabel("End Date:"))
        self.end_date_edit = QDateEdit(calendarPopup=True)
        self.end_date_edit.setDate(QDate.currentDate())  # Default to today
        filter_layout.addWidget(self.end_date_edit)

        apply_filter_btn = QPushButton("Apply Filter")
        apply_filter_btn.setIcon(get_feather_icon("filter", size=16))
        apply_filter_btn.clicked.connect(self.load_sales_data)
        filter_layout.addWidget(apply_filter_btn)
        filter_layout.addStretch()
        main_layout.addLayout(filter_layout)

        # Sales Table
        self.sales_table = QTableWidget()
        # Adding column for brand and making columns count dynamic based on user role
        column_headers = ["ID", "Product", "Brand", "Quantity", "Total Price", "Seller", "Sale Time"]
        if self.current_user['role'] in ['admin', 'manager']:
            column_headers.append("Actions")
            self.sales_table.setColumnCount(8)
        else:
            self.sales_table.setColumnCount(7)
        
        self.sales_table.setHorizontalHeaderLabels(column_headers)
        self.sales_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.sales_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        main_layout.addWidget(self.sales_table)

        self.apply_role_permissions()

    def load_sales_data(self):
        start_date = self.start_date_edit.date()
        end_date = self.end_date_edit.date()

        sales = self.sales_manager.get_sales_reports(start_date, end_date)
        self.sales_table.setRowCount(len(sales))
        
        # Apply table styles using the centralized function
        apply_table_styles(self.sales_table)
        
        # Set larger row heights for better readability
        self.sales_table.verticalHeader().setDefaultSectionSize(50)  # Increase row height
        
        # Make header text larger
        header_font = self.sales_table.horizontalHeader().font()
        header_font.setPointSize(12)  # Larger font
        self.sales_table.horizontalHeader().setFont(header_font)
        
        # Create a base font for all table items
        base_font = self.sales_table.font()
        base_font.setPointSize(12)  # Larger font
        
        for row, sale in enumerate(sales):
            # ID with larger font
            id_item = QTableWidgetItem(str(sale['id']))
            id_item.setFont(base_font)
            self.sales_table.setItem(row, 0, id_item)
            
            # Product Name with larger font
            product_item = QTableWidgetItem(sale['product_name'])
            product_item.setFont(base_font)
            self.sales_table.setItem(row, 1, product_item)
            
            # Brand with larger font
            brand_item = QTableWidgetItem(sale.get('brand', 'N/A'))
            brand_item.setFont(base_font)
            self.sales_table.setItem(row, 2, brand_item)
            
            # Quantity with larger font
            quantity_item = QTableWidgetItem(str(sale['quantity']))
            quantity_item.setFont(base_font)
            self.sales_table.setItem(row, 3, quantity_item)
            
            # Total Price with larger font
            price_item = QTableWidgetItem(f"${sale['total_price']:.2f}")
            price_item.setFont(base_font)
            self.sales_table.setItem(row, 4, price_item)
            
            # Seller with larger font
            seller_item = QTableWidgetItem(sale['seller'])
            seller_item.setFont(base_font)
            self.sales_table.setItem(row, 5, seller_item)
            
            # Format the date/time in a compact way
            sale_datetime = sale['sale_time']
            if isinstance(sale_datetime, str):
                # Format the datetime string if it's already a string
                try:
                    from datetime import datetime
                    dt_obj = datetime.strptime(sale_datetime, "%Y-%m-%d %H:%M:%S")
                    formatted_time = dt_obj.strftime("%Y-%m-%d %H:%M")
                except:
                    formatted_time = sale_datetime
            else:
                # If it's already a datetime object
                formatted_time = sale_datetime.strftime("%Y-%m-%d %H:%M") if hasattr(sale_datetime, 'strftime') else str(sale_datetime)
            
            # Time with larger font
            time_item = QTableWidgetItem(formatted_time)
            time_item.setFont(base_font)
            self.sales_table.setItem(row, 6, time_item)

            # Add an "Undo Sale" button for admin/manager
            if self.current_user['role'] in ['admin', 'manager']:
                undo_btn = QPushButton("Undo")
                undo_btn.setIcon(get_feather_icon("rotate-ccw", size=14))
                undo_btn.clicked.connect(
                    lambda _, s_id=sale['id'], p_name=sale['product_name']: self.undo_sale(s_id, p_name))
                undo_btn.setMinimumHeight(30)  # Taller button

                actions_widget = QWidget()
                actions_layout = QHBoxLayout(actions_widget)
                actions_layout.setContentsMargins(0, 0, 0, 0)
                actions_layout.setSpacing(5)
                actions_layout.addWidget(undo_btn)
                actions_layout.addStretch()
                self.sales_table.setCellWidget(row, 7, actions_widget)  # Column 7 for actions

        # Adjust column widths for better readability
        self.sales_table.resizeColumnsToContents()
        
        # Set minimum column widths to ensure visibility
        min_width = {
            0: 60,    # ID
            1: 220,   # Product name
            2: 150,   # Brand
            3: 100,   # Quantity
            4: 120,   # Price
            5: 150,   # Seller
            6: 150    # Time
        }
        
        for col, width in min_width.items():
            current_width = self.sales_table.columnWidth(col)
            if current_width < width:
                self.sales_table.setColumnWidth(col, width)
        
        # Let the last column (actions or the previous one) stretch
        self.sales_table.horizontalHeader().setStretchLastSection(True)

    @role_required(["admin", "manager"])
    def undo_sale(self, sale_id, product_name):
        reply = QMessageBox.question(self, "Undo Sale",
                                     f"Are you sure you want to undo the sale of '{product_name}'?\n"
                                     "This will restore the product's stock.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            success = self.sales_manager.undo_sale(sale_id)
            if success:
                # Log sale undo
                self.activity_logger.log_activity(
                    user_info=self.current_user,
                    action="Undid Sale",
                    target=product_name,
                    details={"sale_id": sale_id}
                )
                QMessageBox.information(self, "Success", "Sale successfully undone and stock restored.")
                self.load_sales_data()  # Refresh sales table
            else:
                QMessageBox.critical(self, "Error", "Failed to undo sale.")

    def apply_role_permissions(self):
        role = self.current_user['role']
        if role == 'retailer':
            # Retailers can view sales but not undo them
            # The column for actions is conditionally added in load_sales_data()
            pass  # No specific UI elements to hide here, handled by column count