from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
                             QMessageBox, QDialog, QFormLayout, QComboBox,
                             QDoubleSpinBox, QSpinBox, QDateEdit, QFileDialog,
                             QScrollArea, QGridLayout, QFrame, QSizePolicy, QToolButton)
from PyQt6.QtCore import Qt, QDate, QSize, QMargins
from PyQt6.QtGui import QPixmap, QIcon, QFont
import os
from utils.helpers import get_feather_icon, save_product_image, delete_product_image, load_product_image
from utils.config import AppConfig
from utils.decorators import role_required
from utils.styles import get_global_stylesheet, get_product_card_style, get_dialog_style, apply_table_styles

# NOTE: Local ProductManager and ActivityLogger are removed.
# This class now expects API client objects.


class ProductDialog(QDialog):
    """
    Dialog for adding or editing a product, now using API clients.
    It needs a product_client for save operations and a category_client to load categories.
    """
    def __init__(self, product_client, category_client, product_data=None, parent=None):
        super().__init__(parent)
        self.product_client = product_client
        self.category_client = category_client
        self.product_data = product_data
        self.image_path = None # Stores the path of the selected image file

        if product_data:
            self.setWindowTitle(f"Edit Product: {product_data.get('name')}")
        else:
            self.setWindowTitle("Add New Product")
        self.setFixedSize(450, 480) # Increased height for all fields

        self.setStyleSheet(get_dialog_style())
        
        self.init_ui()
        self.load_categories()
        self.load_product_data()

    def init_ui(self):
        form_layout = QFormLayout(self)
        form_layout.setContentsMargins(20, 20, 20, 20)
        form_layout.setSpacing(10)

        self.name_input = QLineEdit()
        form_layout.addRow("Product Name:", self.name_input)

        self.sku_input = QLineEdit()
        form_layout.addRow("SKU:", self.sku_input)

        self.category_combo = QComboBox()
        form_layout.addRow("Category:", self.category_combo)

        self.price_spinbox = QDoubleSpinBox()
        self.price_spinbox.setRange(0.01, 99999.99)
        self.price_spinbox.setPrefix("$")
        self.price_spinbox.setDecimals(2)
        form_layout.addRow("Price:", self.price_spinbox)

        self.stock_spinbox = QSpinBox()
        self.stock_spinbox.setRange(0, 99999)
        form_layout.addRow("Stock Level:", self.stock_spinbox)

        self.expiration_date = QDateEdit()
        self.expiration_date.setCalendarPopup(True)
        self.expiration_date.setDate(QDate.currentDate().addYears(1))
        self.expiration_date.setDisplayFormat("yyyy-MM-dd")
        form_layout.addRow("Expiration Date:", self.expiration_date)
        
        # Image Upload Section
        self.image_label = QLabel("No Image Selected")
        self.image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.image_label.setFixedSize(QSize(100, 100))
        self.image_label.setStyleSheet("border: 1px dashed #95a5a6; background-color: #ecf0f1;")

        image_btn_layout = QHBoxLayout()
        upload_btn = QPushButton("Select Image")
        upload_btn.setIcon(get_feather_icon("image", size=14))
        upload_btn.clicked.connect(self.select_image)
        image_btn_layout.addWidget(upload_btn)
        
        remove_btn = QPushButton("Remove Image")
        remove_btn.setIcon(get_feather_icon("x-circle", size=14))
        remove_btn.clicked.connect(self.remove_image)
        image_btn_layout.addWidget(remove_btn)

        image_h_layout = QHBoxLayout()
        image_h_layout.addWidget(self.image_label)
        image_h_layout.addLayout(image_btn_layout)
        image_h_layout.addStretch()
        
        form_layout.addRow("Image:", image_h_layout)


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

    def load_categories(self):
        """Fetches categories from the API and populates the combobox."""
        # API CALL: GET /categories
        response = self.category_client.list()
        
        if response.success:
            categories = response.data
            self.category_combo.clear()
            self.category_combo.addItem("Select Category", None)
            for category in categories:
                # Store the category ID as item data
                self.category_combo.addItem(category['name'], category['id'])
        else:
            QMessageBox.critical(self, "API Error", f"Failed to load categories: {response.message}")

    def load_product_data(self):
        """Loads data for editing an existing product."""
        if self.product_data:
            self.name_input.setText(self.product_data.get('name', ''))
            self.sku_input.setText(self.product_data.get('sku', ''))
            self.price_spinbox.setValue(self.product_data.get('price', 0.00))
            self.stock_spinbox.setValue(self.product_data.get('stock_level', 0))
            
            # Load category
            category_id = self.product_data.get('category_id')
            index = self.category_combo.findData(category_id)
            if index != -1:
                self.category_combo.setCurrentIndex(index)
            
            # Load expiration date
            date_str = self.product_data.get('expiration_date')
            if date_str:
                self.expiration_date.setDate(QDate.fromString(date_str, "yyyy-MM-dd"))
            
            # Load product image (if image_filename exists)
            image_filename = self.product_data.get('image_filename')
            if image_filename:
                # The image path is constructed using the filename from the database
                self.image_path = os.path.join(AppConfig.PRODUCT_IMAGE_DIR, image_filename)
                pixmap = load_product_image(self.image_path, QSize(100, 100))
                self.image_label.setPixmap(pixmap)
                self.image_label.setText("") # Clear "No Image Selected"

    def select_image(self):
        """Opens a file dialog to select a product image."""
        # Use QFileDialog to allow user to select a file
        file_path, _ = QFileDialog.getOpenFileName(
            self, "Select Product Image", "", 
            "Images (*.png *.jpg *.jpeg *.gif)"
        )
        if file_path:
            self.image_path = file_path
            pixmap = load_product_image(self.image_path, QSize(100, 100))
            self.image_label.setPixmap(pixmap)
            self.image_label.setText("")
    
    def remove_image(self):
        """Clears the selected image."""
        self.image_path = None
        # Set back to placeholder
        self.image_label.setPixmap(QPixmap()) 
        self.image_label.setText("No Image Selected")
        
    def get_product_data(self):
        """Collects and validates product input."""
        name = self.name_input.text().strip()
        sku = self.sku_input.text().strip()
        category_id = self.category_combo.currentData()
        price = self.price_spinbox.value()
        stock_level = self.stock_spinbox.value()
        expiration_date = self.expiration_date.date().toString("yyyy-MM-dd")

        if not name:
            QMessageBox.warning(self, "Input Error", "Product name cannot be empty.")
            return None
        if category_id is None:
            QMessageBox.warning(self, "Input Error", "Please select a category.")
            return None
        if price <= 0:
            QMessageBox.warning(self, "Input Error", "Price must be greater than zero.")
            return None

        data = {
            'name': name,
            'sku': sku if sku else None,
            'category_id': category_id,
            'price': price,
            'stock_level': stock_level,
            'expiration_date': expiration_date
        }
        
        # Include the original ID if editing existing product
        if self.product_data and 'id' in self.product_data:
            data['id'] = self.product_data['id']
            
        # Include image path only if a new one was selected or an existing one is being used
        # Note: The actual image data/file management happens in the calling function
        data['image_local_path'] = self.image_path 
            
        return data


class ProductCard(QFrame):
    """A custom widget representing a product card in the grid view"""
    def __init__(self, product_data, on_edit_callback=None, on_delete_callback=None, parent=None):
        super().__init__(parent)
        self.product_data = product_data
        self.on_edit_callback = on_edit_callback
        self.on_delete_callback = on_delete_callback
        
        # Apply card styling
        self.setObjectName("productCard")
        self.setProperty("class", "product-card")
        self.setStyleSheet(get_product_card_style()) # Apply specific product card styling
        
        # Load image for display
        image_path = os.path.join(AppConfig.PRODUCT_IMAGE_DIR, self.product_data.get('image_filename', ''))
        pixmap = load_product_image(image_path, QSize(120, 120))

        # Setup layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 15, 15, 15)
        layout.setSpacing(10)
        
        # Image
        image_label = QLabel()
        image_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        image_label.setPixmap(pixmap)
        layout.addWidget(image_label)
        
        # Name
        name_label = QLabel(product_data.get('name', 'N/A'))
        name_label.setFont(QFont(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_NORMAL + 2, QFont.Weight.Bold))
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name_label)
        
        # Details (Price / Stock)
        details_label = QLabel(f"${product_data.get('price', 0.00):.2f} | Stock: {product_data.get('stock_level', 0)}")
        details_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        details_label.setStyleSheet("color: #7f8c8d;")
        layout.addWidget(details_label)
        
        # Action Buttons
        button_layout = QHBoxLayout()
        button_layout.setContentsMargins(0, 5, 0, 0)
        
        edit_btn = QPushButton("Edit")
        edit_btn.setIcon(get_feather_icon("edit", size=14))
        edit_btn.clicked.connect(lambda: self.on_edit_callback(self.product_data) if self.on_edit_callback else None)
        button_layout.addWidget(edit_btn)
        
        delete_btn = QPushButton("Delete")
        delete_btn.setIcon(get_feather_icon("trash-2", size=14))
        delete_btn.clicked.connect(lambda: self.on_delete_callback(self.product_data) if self.on_delete_callback else None)
        button_layout.addWidget(delete_btn)
        
        layout.addLayout(button_layout)
        
        self.setFixedWidth(250)


class ProductManagementWidget(QWidget):
    def __init__(self, current_user, product_client, category_client, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        # Inject API clients
        self.product_client = product_client
        self.category_client = category_client # Required for ProductDialog
        # Client-side logging is removed, it is handled by the API server.

        # Apply global style
        self.setStyleSheet(get_global_stylesheet())
        
        self.init_ui()
        self.load_products()
        self.apply_role_permissions()

    def init_ui(self):
        """Initializes the main layout and widgets."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(15)

        # Header and Add Product Button
        header_layout = QHBoxLayout()
        title_label = QLabel("Product Management")
        title_label.setFont(QFont(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_TITLE, QFont.Weight.Bold))
        title_label.setObjectName("widgetTitle")
        header_layout.addWidget(title_label)
        header_layout.addStretch()

        self.add_product_btn = QPushButton("Add New Product")
        self.add_product_btn.setIcon(get_feather_icon("package", size=16))
        self.add_product_btn.clicked.connect(self.add_product)
        header_layout.addWidget(self.add_product_btn)
        main_layout.addLayout(header_layout)

        # Search/Filter and Refresh
        filter_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search products by name or SKU...")
        self.search_input.textChanged.connect(self.filter_products)
        filter_layout.addWidget(self.search_input)
        
        refresh_button = QToolButton()
        refresh_button.setIcon(get_feather_icon("refresh-cw", size=18))
        refresh_button.clicked.connect(self.load_products)
        refresh_button.setToolTip("Refresh Product List")
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

        # Scrollable Area for Product Cards (Grid View)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setObjectName("productScrollArea")
        self.scroll_content = QWidget()
        self.grid_layout = QGridLayout(self.scroll_content)
        self.grid_layout.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        self.grid_layout.setSpacing(20)
        self.scroll_area.setWidget(self.scroll_content)
        main_layout.addWidget(self.scroll_area)
        
    @role_required(["admin", "manager"])
    def load_products(self):
        """Loads all products from the API."""
        # API CALL: GET /products
        response = self.product_client.list()
        
        self.all_products = [] # Store all products for filtering
        
        if response.success:
            self.all_products = response.data
            self.filter_products() # Call filter to populate the grid
        else:
            QMessageBox.critical(self, "API Error", f"Failed to load products: {response.message}")

    def filter_products(self):
        """Filters the displayed products based on search input."""
        search_text = self.search_input.text().lower()

        filtered_products = [
            prod for prod in self.all_products
            if search_text in prod.get('name', '').lower() or search_text in prod.get('sku', '').lower()
        ]
        
        self.display_products(filtered_products)

    def display_products(self, products):
        """Displays products in the grid layout."""
        # Clear existing widgets
        for i in reversed(range(self.grid_layout.count())): 
            widget_to_remove = self.grid_layout.itemAt(i).widget()
            if widget_to_remove:
                widget_to_remove.setParent(None)
        
        column_count = 3 # Define how many cards per row
        
        for index, product in enumerate(products):
            row = index // column_count
            col = index % column_count
            
            card = ProductCard(
                product_data=product,
                on_edit_callback=self.edit_product,
                on_delete_callback=self.delete_product,
                parent=self.scroll_content
            )
            self.grid_layout.addWidget(card, row, col)


    @role_required(["admin", "manager"])
    def add_product(self):
        """Opens a dialog to add a new product and calls the API on success."""
        dialog = ProductDialog(
            product_client=self.product_client, 
            category_client=self.category_client, 
            product_data=None, 
            parent=self
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            new_data = dialog.get_product_data()
            if new_data:
                image_local_path = new_data.pop('image_local_path', None)
                
                # API CALL: POST /products
                response = self.product_client.create(new_data)
                
                if response.success:
                    # After successful creation, save the image file locally 
                    # using the ID returned from the server for the filename
                    product_id = response.data.get('id')
                    if image_local_path and product_id:
                        # Save the image to the local assets folder using the product ID
                        save_product_image(image_local_path, product_id)

                    QMessageBox.information(self, "Success", f"Product '{new_data['name']}' created successfully.")
                    # Logging is handled by the API server
                    self.load_products()
                else:
                    QMessageBox.critical(self, "API Error", f"Failed to create product: {response.message}")

    @role_required(["admin", "manager"])
    def edit_product(self, product_data):
        """Opens a dialog to edit an existing product and calls the API on success."""
        dialog = ProductDialog(
            product_client=self.product_client, 
            category_client=self.category_client, 
            product_data=product_data, 
            parent=self
        )
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_data = dialog.get_product_data()
            if updated_data and 'id' in updated_data:
                product_id = updated_data.pop('id')
                name = updated_data['name']
                image_local_path = updated_data.pop('image_local_path', None)

                # API CALL: PUT /products/<id>
                response = self.product_client.update(product_id, updated_data)
                
                if response.success:
                    # Handle image update locally
                    if image_local_path:
                        # Save new image or update existing one
                        save_product_image(image_local_path, product_id)
                    elif 'image_filename' in product_data and image_local_path is None:
                        # Check if user removed the image in the dialog
                        # This should be handled by a specific flag in the API call, 
                        # but for client-side file cleanup:
                        delete_product_image(product_data['image_filename'])
                    
                    QMessageBox.information(self, "Success", f"Product '{name}' updated successfully.")
                    # Logging is handled by the API server
                    self.load_products()
                else:
                    QMessageBox.critical(self, "API Error", f"Failed to update product: {response.message}")

    @role_required(["admin", "manager"])
    def delete_product(self, product_data):
        """Prompts for confirmation and calls the API to delete a product."""
        product_id = product_data.get('id')
        name = product_data.get('name')
        image_filename = product_data.get('image_filename')

        reply = QMessageBox.question(self, "Confirm Delete",
                                     f"Are you sure you want to delete product '{name}' (ID: {product_id})?",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)

        if reply == QMessageBox.StandardButton.Yes:
            # API CALL: DELETE /products/<id>
            response = self.product_client.delete(product_id)
            
            if response.success:
                # On successful server-side delete, remove the local image file
                if image_filename:
                    delete_product_image(image_filename)
                    
                QMessageBox.information(self, "Success", f"Product '{name}' deleted successfully.")
                # Logging is handled by the API server
                self.load_products()
            else:
                QMessageBox.critical(self, "API Error", f"Failed to delete product: {response.message}")

    def apply_role_permissions(self):
        """Adjusts UI elements based on the current user's role."""
        role = self.current_user.get('role', 'retailer')
        is_allowed = role in ['admin', 'manager']

        self.add_product_btn.setVisible(is_allowed)
        # Note: Card buttons (Edit/Delete) visibility/functionality is controlled
        # by the permissions check inside the respective methods via @role_required.