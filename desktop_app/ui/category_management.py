from PyQt6.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel,
                             QLineEdit, QPushButton, QTableWidget, QTableWidgetItem,
                             QMessageBox, QDialog, QFormLayout, QScrollArea, QGridLayout, QFrame)
from PyQt6.QtCore import Qt
from core.product_manager import ProductManager  # Category management is part of ProductManager
from core.activity_logger import ActivityLogger
from utils.helpers import get_feather_icon
from utils.config import AppConfig
from utils.decorators import role_required
from utils.styles import get_global_stylesheet, get_category_card_style, get_dialog_style  # Import style functions


class CategoryCard(QFrame):
    """A custom widget representing a category card in the grid view"""
    def __init__(self, category_data, on_edit_callback=None, on_delete_callback=None, parent=None):
        super().__init__(parent)
        self.category_data = category_data
        
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
        icon_label.setPixmap(get_feather_icon("folder", size=64).pixmap(64, 64))
        layout.addWidget(icon_label, alignment=Qt.AlignmentFlag.AlignCenter)
        
        # Category name
        name_label = QLabel(category_data['name'])
        name_label.setProperty("class", "category-title")
        name_label.setWordWrap(True)
        name_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(name_label)
        
        # Category ID
        id_label = QLabel(f"ID: {category_data['id']}")
        id_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        id_label.setStyleSheet(f"color: {AppConfig.TEXT_COLOR_ALT};")
        layout.addWidget(id_label)
        
        layout.addStretch()
        
        # Action buttons
        if on_edit_callback or on_delete_callback:
            buttons_layout = QHBoxLayout()
            
            if on_edit_callback:
                edit_btn = QPushButton("Edit")
                edit_btn.setIcon(get_feather_icon("edit", size=14))
                edit_btn.clicked.connect(lambda: on_edit_callback(category_data))
                buttons_layout.addWidget(edit_btn)
            
            if on_delete_callback:
                delete_btn = QPushButton("Delete")
                delete_btn.setIcon(get_feather_icon("trash-2", size=14))
                delete_btn.clicked.connect(lambda: on_delete_callback(category_data['id'], 
                                                                   category_data['name']))
                buttons_layout.addWidget(delete_btn)
                
            layout.addLayout(buttons_layout)
        
        # Set fixed size for consistent card sizing
        self.setFixedSize(180, 250)


class CategoryManagementWidget(QWidget):
    def __init__(self, current_user, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.product_manager = ProductManager()
        self.activity_logger = ActivityLogger() # Initialize logger

        self.setStyleSheet(get_global_stylesheet()) # Apply global styles
        self.init_ui()
        self.load_categories()

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # Header section with title and add button
        header_layout = QHBoxLayout()
        title_label = QLabel("Category Management")
        title_label.setStyleSheet(f"font-size: {AppConfig.FONT_SIZE_XLARGE}pt; font-weight: bold;")
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Add Category Button
        self.add_category_btn = QPushButton("Add New Category")
        self.add_category_btn.setObjectName("addCategoryButton")
        self.add_category_btn.setIcon(get_feather_icon("plus", size=16))
        self.add_category_btn.clicked.connect(self.add_category)
        header_layout.addWidget(self.add_category_btn)
        
        main_layout.addLayout(header_layout)
        
        # Search bar
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("Search Categories:"))
        
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type to search categories...")
        self.search_input.textChanged.connect(self.filter_categories)
        search_layout.addWidget(self.search_input)
        
        main_layout.addLayout(search_layout)

        # Scroll area for category cards grid
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        
        # Container widget for grid layout
        self.grid_container = QWidget()
        self.grid_layout = QGridLayout(self.grid_container)
        self.grid_layout.setContentsMargins(0, 0, 0, 0)
        self.grid_layout.setSpacing(15)
        
        self.scroll_area.setWidget(self.grid_container)
        main_layout.addWidget(self.scroll_area)

        self.apply_role_permissions()

    def load_categories(self):
        categories = self.product_manager.get_categories()
        self.all_categories = categories  # Store for filtering
        self.display_categories(categories)
    
    def filter_categories(self):
        """Filter categories based on search text"""
        search_text = self.search_input.text().lower()
        if not search_text:
            # If search is empty, show all categories
            self.display_categories(self.all_categories)
        else:
            # Filter categories based on search text
            filtered_categories = [cat for cat in self.all_categories 
                                 if search_text in cat['name'].lower()]
            self.display_categories(filtered_categories)
    
    def display_categories(self, categories):
        """Display category cards in grid layout"""
        # Clear existing category cards
        while self.grid_layout.count():
            item = self.grid_layout.takeAt(0)
            widget = item.widget()
            if widget:
                widget.deleteLater()
        
        # Set up grid parameters
        cards_per_row = 4  # Adjust based on preferred layout
        
        # Create category cards and add to grid
        for i, category in enumerate(categories):
            row = i // cards_per_row
            col = i % cards_per_row
            
            # Determine if edit/delete callbacks should be enabled based on role
            edit_callback = self.edit_category if self.current_user['role'] in ['admin', 'manager'] else None
            delete_callback = self.delete_category if self.current_user['role'] in ['admin', 'manager'] else None
            
            category_card = CategoryCard(category, edit_callback, delete_callback)
            self.grid_layout.addWidget(category_card, row, col)
        
        # Add empty widgets to fill the last row if needed
        total_items = len(categories)
        if total_items % cards_per_row != 0:
            remaining = cards_per_row - (total_items % cards_per_row)
            for i in range(remaining):
                empty_widget = QWidget()
                self.grid_layout.addWidget(empty_widget, total_items // cards_per_row, 
                                         (total_items % cards_per_row) + i)
                
        # If no categories, show a message
        if not categories:
            no_categories_label = QLabel("No categories found. Add a new category to get started.")
            no_categories_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_categories_label.setStyleSheet("font-size: 14pt; color: rgba(255,255,255,0.5); padding: 20px;")
            self.grid_layout.addWidget(no_categories_label, 0, 0, 1, cards_per_row)

    @role_required(["admin", "manager"])
    def add_category(self, *args):
        # Ignore any extra positional arguments that might be passed
        dialog = CategoryDialog(parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            category_name = dialog.get_category_name()
            if category_name:
                success = self.product_manager.add_category(category_name)
                if success:
                    # Log category creation
                    self.activity_logger.log_activity(
                        user_info=self.current_user,
                        action="CATEGORY_ADDED",
                        target=category_name,
                        details={"created_by_role": self.current_user.get("role")}
                    )
                    QMessageBox.information(self, "Success", "Category added successfully.")
                    self.load_categories()
                else:
                    QMessageBox.critical(self, "Error", "Failed to add category. Name might already exist.")

    @role_required(["admin", "manager"])
    def edit_category(self, category_data):
        dialog = CategoryDialog(category_data=category_data, parent=self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            updated_name = dialog.get_category_name()
            if updated_name:
                success = self.product_manager.update_category(category_data['id'], updated_name)
                if success:
                    # Log category update
                    self.activity_logger.log_activity(
                        user_info=self.current_user,
                        action="CATEGORY_UPDATED",
                        target=updated_name,
                        details={
                            "category_id": category_data['id'],
                            "old_name": category_data['name'],
                            "updated_by_role": self.current_user.get("role")
                        }
                    )
                    QMessageBox.information(self, "Success", "Category updated successfully.")
                    self.load_categories()
                else:
                    QMessageBox.critical(self, "Error", "Failed to update category. Name might already exist.")

    @role_required(["admin", "manager"])
    def delete_category(self, category_id, category_name):
        reply = QMessageBox.question(self, "Delete Category",
                                     f"Are you sure you want to delete category '{category_name}'?\n"
                                     "Note: You cannot delete categories with linked products.",
                                     QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            success = self.product_manager.delete_category(category_id)
            if success:
                # Log category deletion
                self.activity_logger.log_activity(
                    user_info=self.current_user,
                    action="CATEGORY_DELETED",
                    target=category_name,
                    details={
                        "category_id": category_id,
                        "deleted_by_role": self.current_user.get("role")
                    }
                )
                QMessageBox.information(self, "Success", "Category deleted successfully.")
                self.load_categories()
            # Error message for linked products is handled inside db_manager.delete_category
            # so no else block here for that specific error.

    def apply_role_permissions(self):
        role = self.current_user['role']
        if role == 'retailer':  # Retailers can only view categories
            if hasattr(self, 'add_category_btn'):
                self.add_category_btn.hide()


class CategoryDialog(QDialog):
    def __init__(self, category_data=None, parent=None):
        super().__init__(parent)
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

    def get_category_name(self):
        name = self.name_input.text().strip()
        if not name:
            QMessageBox.warning(self, "Input Error", "Category Name cannot be empty.")
            return None
        return name