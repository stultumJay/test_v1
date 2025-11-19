from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
                             QMessageBox, QDialog, QFormLayout, QScrollArea, QGridLayout, QFrame,
                             QToolButton, QSizePolicy)
from PyQt6.QtCore import Qt, QSize
from PyQt6.QtGui import QFont
from utils.helpers import get_feather_icon
from utils.config import AppConfig
from utils.decorators import role_required
from utils.styles import get_global_stylesheet, get_category_card_style, get_dialog_style

# NOTE: Local ProductManager and ActivityLogger are removed.
# This class now expects API client objects.


class CategoryDialog(QDialog):
    """
    Dialog for adding or editing a category, now using an API client.
    """
    def __init__(self, category_client, category_data=None, parent=None):
        super().__init__(parent)
        self.category_client = category_client
        self.category_data = category_data

        if category_data:
            self.setWindowTitle(f"Edit Category: {category_data.get('name')}")
        else:
            self.setWindowTitle("Add New Category")
        self.setFixedSize(300, 150)

        # Apply dialog style
        self.setStyleSheet(get_dialog_style())
        
        self.init_ui()
        self.load_category_data()

    def init_ui(self):
        form_layout = QFormLayout(self)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(10)

        self.name_input = QLineEdit()
        form_layout.addRow("Category Name:", self.name_input)

        button_box = QHBoxLayout()
        ok_button = QPushButton("Save")
        ok_button.setIcon(get_feather_icon("check-circle", size=16))
        ok_button.clicked.connect(self.accept)
        cancel_button = QPushButton("Cancel")
        cancel_button.setIcon(get_feather_icon("x", size=16))
        cancel_button.clicked.connect(self.reject)
        button_box.addStretch()
        button_box.addWidget(ok_button)
        button_box.addWidget(cancel_button)
        form_layout.addRow(button_box)

    def load_category_data(self):
        if self.category_data:
            self.name_input.setText(self.category_data.get('name', ''))

    def get_category_data(self):
        """Collects and validates category input."""
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Input Error", "Category name cannot be empty.")
            return None
        
        data = {'name': name}
        
        # Include ID if editing
        if self.category_data and 'id' in self.category_data:
            data['id'] = self.category_data['id']
            
        return data


class CategoryCard(QFrame):
    """A custom widget representing a category card in the grid view"""
    def __init__(self, category_data, product_count, on_edit_callback=None, on_delete_callback=None, parent=None):
        super().__init__(parent)
        self.category_data = category_data
        self.product_count = product_count
        self.on_edit_callback = on_edit_callback
        self.on_delete_callback = on_delete_callback
        
        # Apply card styling
        self.setObjectName("categoryCard")
        self.setProperty("class", "category-card")
        
        # Apply category card style
        self.setStyleSheet(get_category_card_style())
        
        # Setup layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Category icon
        icon_label = QLabel()
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_label.setPixmap(get_feather_icon("folder", size=32).pixmap(QSize(32, 32)))
        layout.addWidget(icon_label)
        
        # Category Name
        name_label = QLabel(category_data.get('name', 'N/A'))
        name_label.setFont(QFont(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_NORMAL + 2, QFont.Weight.Bold))
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name_label)
        
        # Product Count
        count_label = QLabel(f"{self.product_count} Products")
        count_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        count_label.setStyleSheet("color: #7f8c8d;")
        layout.addWidget(count_label)
        
        # Action Buttons
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 5, 0, 0)
        
        edit_btn = QPushButton("Edit")
        edit_btn.setIcon(get_feather_icon("edit", size=14))
        edit_btn.clicked.connect(lambda: self.on_edit_callback(self.category_data) if self.on_edit_callback else None)
        button_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("Delete")
        delete_btn.setIcon(get_feather_icon("trash-2", size=14))
        delete_btn.clicked.connect(lambda: self.on_delete_callback(self.category_data, self.product_count) if self.on_delete_callback else None)
        button_layout.addWidget(delete_btn)
        
        layout.addLayout(button_layout)
        
        # Ensure the card takes minimum space but is centered/aligned
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Fixed)
        self.setFixedWidth(200) # Set a fixed width for the card


class CategoryManagementWidget(QWidget):
    def __init__(self, current_user, category_client, product_client, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        # Inject API clients
        self.category_client = category_client
        self.product_client = product_client # Used to fetch product counts
        # Client-side logging is removed, it is handled by the API server.

        # Apply global style
        self.setStyleSheet(get_global_stylesheet())
        
        self.init_ui()
        self.load_categories()
        self.apply_role_permissions()

    def init_ui(self):
        """Initializes the main layout and widgets."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Header and Add Category Button
        header_layout = QHBoxLayout()
        title_label = QLabel("Category Management")
        title_label.setFont(QFont(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_TITLE, QFont.Weight.Bold))
        title_label.setObjectName("widgetTitle")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        self.add_category_btn = QPushButton("Add New Category")
        self.add_category_btn.setIcon(get_feather_icon("folder-plus", size=16))
        self.add_category_btn.clicked.connect(self.add_category)
        header_layout.addWidget(self.add_category_btn)
        main_layout.addLayout(header_layout)

        # Search/Filter and Refresh
        filter_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search categories...")
        self.search_input.textChanged.connect(self.filter_categories)
        filter_layout.addWidget(self.search_input)
        
        refresh_button = QToolButton()
        refresh_button.setIcon(get_feather_icon("refresh-cw", size=18))
        refresh_button.clicked.connect(self.load_categories)
        refresh_button.setToolTip("Refresh Category List")
        refresh_button.setStyleSheet("""
            QToolButton { 
                border: none; 
                padding: 8px;
                border-radius: 8px;
            }
            QToolButton:hover {
                background-color: #e0e0e0;
            }
        """)
        filter_layout.addWidget(refresh_button)
        main_layout.addLayout(filter_layout)


        # Scrollable Area for Category Cards
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setObjectName("categoryScrollArea")
        self.scroll_content = QWidget()
        self.grid_layout = QGridLayout(self.scroll_content)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.grid_layout.setSpacing(20)
        self.scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll_area)
        
        # List view option (basic table for completeness)
        self.category_table = QTableWidget()
        self.category_table.setColumnCount(3)
        self.category_table.setHorizontalHeaderLabels(["ID", "Category Name", "Actions"])
        # self.category_table.setVisible(False) # Start with grid view

    @role_required(["admin", "manager"])
    def load_categories(self):
        """Loads categories and product counts from the API."""
        
        # API CALL 1: GET /categories
        categories_response = self.category_client.list()
        
        # API CALL 2: Get all products to count per category (for simplicity, a dedicated
        # API endpoint for counts is usually better, but we assume basic client structure)
        products_response = self.product_client.list()
        
        self.all_categories = []
        product_counts = {}
        
        if categories_response.success:
            self.all_categories = categories_response.data
        else:
            QMessageBox.critical(self, "API Error", f"Failed to load categories: {categories_response.message}")
            return
            
        if products_response.success:
            # Calculate product counts per category
            for product in products_response.data:
                cat_id = product.get('category_id')
                if cat_id is not None:
                    product_counts[cat_id] = product_counts.get(cat_id, 0) + 1
        else:
             QMessageBox.warning(self, "Data Warning", "Could not load product data to count products per category.")
        
        self.product_counts = product_counts
        self.filter_categories()


    def filter_categories(self):
        """Filters the displayed categories based on search input."""
        search_text = self.search_input.text().lower()

        filtered_categories = [
            cat for cat in self.all_categories
            if search_text in cat.get('name', '').lower()
        ]
        
        self.display_categories(filtered_categories)

    def display_categories(self, categories):
        """Displays categories in the grid layout."""
        # Clear existing widgets
        for i in reversed(range(self.grid_layout.count())): 
            widget_to_remove = self.grid_layout.itemAt(i).widget()
            if widget_to_remove:
                widget_to_remove.setParent(None)
        
        column_count = 4 # Define how many cards per row
        
        for index, category in enumerate(categories):
            row = index // column_count
            col = index % column_count
            
            cat_id = category.get('id')
            # Get the pre-calculated count, default to 0
            count = self.product_counts.get(cat_id, 0) 
            
            card = CategoryCard(
                category_data=category,
                product_count=count,
                on_edit_callback=self.edit_category,
                on_delete_callback=self.delete_category,
                parent=self.scroll_content
            )
            self.grid_layout.addWidget(card, row, col)

    @role_required(["admin", "manager"])
    def add_category(self):
        """Opens a dialog to add a new category and calls the API on success."""
        dialog = CategoryDialog(category_client=self.category_client, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_data = dialog.get_category_data()
            if new_data:
                # API CALL: POST /categories
                response = self.category_client.create(new_data)
                
                if response.success:
                    QMessageBox.information(self, "Success", f"Category '{new_data['name']}' created successfully.")
                    # Logging is handled by the API server
                    self.load_categories()
                else:
                    QMessageBox.critical(self, "API Error", f"Failed to create category: {response.message}")

    @role_required(["admin", "manager"])
    def edit_category(self, category_data):
        """Opens a dialog to edit an existing category and calls the API on success."""
        dialog = CategoryDialog(category_client=self.category_client, category_data=category_data, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_data = dialog.get_category_data()
            if updated_data and 'id' in updated_data:
                category_id = updated_data.pop('id')
                name = updated_data['name']

                # API CALL: PUT /categories/<id>
                response = self.category_client.update(category_id, updated_data)
                
                if response.success:
                    QMessageBox.information(self, "Success", f"Category '{name}' updated successfully.")
                    # Logging is handled by the API server
                    self.load_categories()
                else:
                    QMessageBox.critical(self, "API Error", f"Failed to update category: {response.message}")

    @role_required(["admin", "manager"])
    def delete_category(self, category_data, product_count):
        """Prompts for confirmation and calls the API to delete a category."""
        category_id = category_data.get('id')
        name = category_data.get('name')

        if product_count > 0:
            QMessageBox.warning(self, "Deletion Forbidden", 
                                f"Cannot delete category '{name}' because it is linked to {product_count} product(s). "
                                "Please update or delete those products first.")
            return

        reply = QMessageBox.question(self, "Confirm Delete",
                                     f"Are you sure you want to delete category '{name}' (ID: {category_id})?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            # API CALL: DELETE /categories/<id>
            response = self.category_client.delete(category_id)
            
            if response.success:
                QMessageBox.information(self, "Success", f"Category '{name}' deleted successfully.")
                # Logging is handled by the API server
                self.load_categories()
            else:
                QMessageBox.critical(self, "API Error", f"Failed to delete category: {response.message}")

    def apply_role_permissions(self):
        """Adjusts UI elements based on the current user's role."""
        role = self.current_user.get('role', 'retailer')
        is_allowed = role in ['admin', 'manager']

        self.add_category_btn.setVisible(is_allowed)
        
        # Note: Card buttons (Edit/Delete) visibility/functionality is controlled
        # by the permissions check inside the respective methods via @role_required.