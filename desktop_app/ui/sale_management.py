from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
                             QMessageBox, QDialog, QFormLayout, QComboBox,
                             QDateEdit, QHeaderView)
from PyQt6.QtCore import Qt, QDate
from utils.helpers import get_feather_icon
from utils.config import AppConfig
from utils.decorators import role_required
from utils.styles import get_global_stylesheet, apply_table_styles

# NOTE: Local SalesManager, ProductManager, and ActivityLogger are removed.
# This class now expects API client objects.


class SalesManagementWidget(QWidget):
    def __init__(self, current_user, sales_client, product_client, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        # Inject API clients
        self.sales_client = sales_client
        self.product_client = product_client  # To fetch product names for sales display
        # Client-side logging is removed, it is handled by the API server.

        # Apply global style
        self.setStyleSheet(get_global_stylesheet())
        
        self.init_ui()
        self.load_sales_data()  # Initial load
        self.apply_role_permissions()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Header and Refresh Button
        header_layout = QHBoxLayout()
        title_label = QLabel("Sales History")
        title_label.setFont(QFont(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_TITLE, QFont.Weight.Bold))
        title_label.setObjectName("widgetTitle")
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        
        refresh_button = QPushButton("Refresh")
        refresh_button.setIcon(get_feather_icon("refresh-cw", size=16))
        refresh_button.clicked.connect(self.load_sales_data)
        header_layout.addWidget(refresh_button)
        main_layout.addLayout(header_layout)

        # Date Filters
        filter_layout = QHBoxLayout()
        filter_layout.addWidget(QLabel("Start Date:"))
        self.start_date_edit = QDateEdit()
        self.start_date_edit.setCalendarPopup(True)
        self.start_date_edit.setDate(QDate.currentDate().addMonths(-1)) # Default to last month
        self.start_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.start_date_edit.dateChanged.connect(self.load_sales_data)
        filter_layout.addWidget(self.start_date_edit)
        
        filter_layout.addWidget(QLabel("End Date:"))
        self.end_date_edit = QDateEdit()
        self.end_date_edit.setCalendarPopup(True)
        self.end_date_edit.setDate(QDate.currentDate())
        self.end_date_edit.setDisplayFormat("yyyy-MM-dd")
        self.end_date_edit.dateChanged.connect(self.load_sales_data)
        filter_layout.addWidget(self.end_date_edit)
        
        filter_layout.addStretch()
        main_layout.addLayout(filter_layout)

        # Sales Table
        self.sales_table = QTableWidget()
        apply_table_styles(self.sales_table)
        main_layout.addWidget(self.sales_table)


    @role_required([AppConfig.ROLE_ADMIN, AppConfig.ROLE_MANAGER, AppConfig.ROLE_RETAILER])
    def load_sales_data(self):
        """Loads sales data within the specified date range from the API."""
        start_date = self.start_date_edit.date().toString("yyyy-MM-dd")
        end_date = self.end_date_edit.date().toString("yyyy-MM-dd")
        
        # API CALL: GET /sales?start_date=...&end_date=...
        response = self.sales_client.list(start_date=start_date, end_date=end_date)
        
        if not response.success:
            QMessageBox.critical(self, "API Error", f"Failed to load sales data: {response.message}")
            self.sales_table.setRowCount(0)
            return

        sales_list = response.data
        
        # Determine columns based on user role
        role = self.current_user.get('role', 'retailer')
        is_admin_or_manager = role in ['admin', 'manager']
        
        column_labels = ["Sale ID", "Date/Time", "Product", "Quantity", "Total Price", "Retailer ID"]
        if is_admin_or_manager:
            column_labels.append("Actions")
        
        self.sales_table.setColumnCount(len(column_labels))
        self.sales_table.setHorizontalHeaderLabels(column_labels)
        self.sales_table.setRowCount(len(sales_list))

        for row, sale in enumerate(sales_list):
            # Format datetime
            datetime_str = sale.get('created_at', 'N/A')
            
            # Format currency
            total_price_str = f"${sale.get('total_price', 0.00):.2f}"

            # API response should ideally contain product name, but we fallback if only ID is present
            product_name = sale.get('product_name', f"ID: {sale.get('product_id', 'N/A')}")
            
            data = [
                str(sale.get('id', '')),
                datetime_str,
                product_name,
                str(sale.get('quantity', 0)),
                total_price_str,
                str(sale.get('retailer_id', 'N/A'))
            ]

            for col, item_data in enumerate(data):
                item = QTableWidgetItem(item_data)
                # Align text for numeric/ID columns
                if col in [0, 3, 4, 5]: 
                    item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.sales_table.setItem(row, col, item)

            # Actions column for Admin/Manager to undo sale
            if is_admin_or_manager:
                undo_btn = QPushButton("Undo")
                undo_btn.setIcon(get_feather_icon("corner-up-left", size=14))
                undo_btn.clicked.connect(lambda _, s=sale: self.undo_sale(s['id'], product_name))
                
                action_widget = QWidget()
                action_layout = QHBoxLayout(action_widget)
                action_layout.setContentsMargins(5, 5, 5, 5)
                action_layout.addWidget(undo_btn)
                action_layout.addStretch()

                self.sales_table.setCellWidget(row, len(column_labels) - 1, action_widget)
        
        self.sales_table.resizeColumnsToContents()
        self.sales_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)


    @role_required(["admin", "manager"])
    def undo_sale(self, sale_id, product_name):
        """Prompts for confirmation and calls the API to undo a sale."""
        reply = QMessageBox.question(self, "Undo Sale",
                                     f"Are you sure you want to undo the sale of '{product_name}'?\\n"
                                     "This will restore the product's stock.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            # API CALL: POST /sales/undo/<id> (or PUT /sales/<id> with status update)
            # Assuming a dedicated undo endpoint
            response = self.sales_client.undo(sale_id)
            
            if response.success:
                # Logging is handled by the API server when the transaction is reversed
                QMessageBox.information(self, "Success", "Sale successfully undone and stock restored.")
                self.load_sales_data()  # Refresh sales table
            else:
                QMessageBox.critical(self, "API Error", f"Failed to undo sale: {response.message}")

    def apply_role_permissions(self):
        """Adjusts the layout based on the current user's role (mainly handled in load_sales_data)."""
        # The main permission check is done in load_sales_data when setting up the table and actions
        pass