"""
Unified Styling System for StockaDoodle Desktop App
Provides consistent theming, QSS stylesheets, and helper functions
"""

from PyQt6.QtWidgets import QTableWidget, QMessageBox
from utils.config import AppConfig


def get_global_stylesheet() -> str:
    """
    Get the global application stylesheet
    Apply to QApplication or main window
    """
    return f"""
        /* Global Styles */
        QWidget {{
            background-color: {AppConfig.BACKGROUND_COLOR};
            color: {AppConfig.TEXT_COLOR};
            font-family: {AppConfig.FONT_FAMILY};
            font-size: {AppConfig.FONT_SIZE_NORMAL}pt;
        }}
        
        /* Labels */
        QLabel {{
            color: {AppConfig.TEXT_COLOR};
        }}
        
        QLabel#Title {{
            font-size: {AppConfig.FONT_SIZE_XLARGE}pt;
            font-weight: bold;
            color: white;
        }}
        
        QLabel#Header {{
            font-size: {AppConfig.FONT_SIZE_LARGE}pt;
            font-weight: bold;
            color: {AppConfig.TEXT_COLOR};
        }}
        
        /* Input Fields */
        QLineEdit, QTextEdit, QPlainTextEdit {{
            background-color: {AppConfig.CARD_BACKGROUND};
            border: 1px solid #555;
            border-radius: 6px;
            padding: 8px;
            color: {AppConfig.TEXT_COLOR};
            selection-background-color: {AppConfig.PRIMARY_COLOR};
        }}
        
        QLineEdit:focus, QTextEdit:focus {{
            border: 1px solid {AppConfig.PRIMARY_COLOR};
        }}
        
        /* Combo Boxes */
        QComboBox {{
            background-color: {AppConfig.CARD_BACKGROUND};
            border: 1px solid #555;
            border-radius: 6px;
            padding: 8px;
            color: {AppConfig.TEXT_COLOR};
            min-height: 25px;
        }}
        
        QComboBox:hover {{
            border: 1px solid {AppConfig.PRIMARY_COLOR};
        }}
        
        QComboBox::drop-down {{
            border: none;
            width: 20px;
        }}
        
        QComboBox::down-arrow {{
            image: none;
            border-left: 5px solid transparent;
            border-right: 5px solid transparent;
            border-top: 5px solid {AppConfig.TEXT_COLOR};
            margin-right: 5px;
        }}
        
        QComboBox QAbstractItemView {{
            background-color: {AppConfig.CARD_BACKGROUND};
            border: 1px solid {AppConfig.PRIMARY_COLOR};
            selection-background-color: {AppConfig.PRIMARY_COLOR};
            color: {AppConfig.TEXT_COLOR};
        }}
        
        /* Buttons */
        QPushButton {{
            background-color: {AppConfig.PRIMARY_COLOR};
            color: white;
            border: none;
            border-radius: 6px;
            padding: 10px 20px;
            font-weight: bold;
            font-size: {AppConfig.FONT_SIZE_NORMAL}pt;
        }}
        
        QPushButton:hover {{
            background-color: {AppConfig.SECONDARY_COLOR};
        }}
        
        QPushButton:pressed {{
            background-color: #5a4dbf;
        }}
        
        QPushButton:disabled {{
            background-color: #555;
            color: #888;
        }}
        
        /* Sidebar Navigation Buttons */
        QPushButton[class="SidebarButton"] {{
            background-color: transparent;
            color: #aaa;
            text-align: left;
            padding: 12px 15px;
            border: none;
            border-radius: 8px;
            font-size: 11pt;
        }}
        
        QPushButton[class="SidebarButton"]:hover {{
            background-color: rgba(255, 255, 255, 0.1);
            color: white;
        }}
        
        QPushButton[class="SidebarButton"]:checked {{
            background-color: {AppConfig.PRIMARY_COLOR};
            color: white;
        }}
        
        /* Scroll Areas */
        QScrollArea {{
            border: none;
            background-color: transparent;
        }}
        
        QScrollBar:vertical {{
            border: none;
            background: rgba(0, 0, 0, 0.2);
            width: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:vertical {{
            background: {AppConfig.PRIMARY_COLOR};
            border-radius: 6px;
            min-height: 20px;
        }}
        
        QScrollBar::handle:vertical:hover {{
            background: {AppConfig.SECONDARY_COLOR};
        }}
        
        QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
            height: 0px;
        }}
        
        QScrollBar:horizontal {{
            border: none;
            background: rgba(0, 0, 0, 0.2);
            height: 12px;
            border-radius: 6px;
        }}
        
        QScrollBar::handle:horizontal {{
            background: {AppConfig.PRIMARY_COLOR};
            border-radius: 6px;
            min-width: 20px;
        }}
        
        /* Tab Widgets */
        QTabWidget::pane {{
            border: 1px solid #555;
            border-radius: 8px;
            background-color: {AppConfig.CARD_BACKGROUND};
        }}
        
        QTabBar::tab {{
            background-color: #2A2A2A;
            color: #aaa;
            padding: 10px 20px;
            border-top-left-radius: 8px;
            border-top-right-radius: 8px;
            margin-right: 2px;
        }}
        
        QTabBar::tab:selected {{
            background-color: {AppConfig.CARD_BACKGROUND};
            color: white;
        }}
        
        QTabBar::tab:hover {{
            background-color: #3A3A3A;
        }}
        
        /* Frames and Cards */
        QFrame#Card {{
            background-color: {AppConfig.CARD_BACKGROUND};
            border-radius: 12px;
            padding: 20px;
        }}
        
        /* Check Boxes */
        QCheckBox {{
            color: {AppConfig.TEXT_COLOR};
            spacing: 8px;
        }}
        
        QCheckBox::indicator {{
            width: 18px;
            height: 18px;
            border: 2px solid #555;
            border-radius: 4px;
            background-color: {AppConfig.CARD_BACKGROUND};
        }}
        
        QCheckBox::indicator:checked {{
            background-color: {AppConfig.PRIMARY_COLOR};
            border-color: {AppConfig.PRIMARY_COLOR};
        }}
        
        /* Spin Boxes */
        QSpinBox, QDoubleSpinBox {{
            background-color: {AppConfig.CARD_BACKGROUND};
            border: 1px solid #555;
            border-radius: 6px;
            padding: 8px;
            color: {AppConfig.TEXT_COLOR};
        }}
        
        QSpinBox::up-button, QDoubleSpinBox::up-button {{
            subcontrol-origin: border;
            subcontrol-position: top right;
            width: 20px;
            border-left: 1px solid #555;
            background-color: #3A3A3A;
        }}
        
        QSpinBox::down-button, QDoubleSpinBox::down-button {{
            subcontrol-origin: border;
            subcontrol-position: bottom right;
            width: 20px;
            border-left: 1px solid #555;
            background-color: #3A3A3A;
        }}
        
        /* Date Edit */
        QDateEdit {{
            background-color: {AppConfig.CARD_BACKGROUND};
            border: 1px solid #555;
            border-radius: 6px;
            padding: 8px;
            color: {AppConfig.TEXT_COLOR};
        }}
    """


def apply_table_styles(table: QTableWidget):
    """
    Apply consistent styling to QTableWidget
    
    Args:
        table: QTableWidget instance to style
    """
    table.setStyleSheet(f"""
        QTableWidget {{
            background-color: {AppConfig.CARD_BACKGROUND};
            color: {AppConfig.TEXT_COLOR};
            gridline-color: #444;
            border: 1px solid #555;
            border-radius: 8px;
        }}
        
        QTableWidget::item {{
            padding: 8px;
            border: none;
        }}
        
        QTableWidget::item:selected {{
            background-color: {AppConfig.PRIMARY_COLOR};
            color: white;
        }}
        
        QTableWidget::item:hover {{
            background-color: rgba(108, 92, 231, 0.3);
        }}
        
        QHeaderView::section {{
            background-color: {AppConfig.PRIMARY_COLOR};
            color: white;
            padding: 10px;
            border: none;
            border-right: 1px solid #555;
            border-bottom: 1px solid #555;
            font-weight: bold;
            font-size: {AppConfig.FONT_SIZE_NORMAL}pt;
        }}
        
        QHeaderView::section:first {{
            border-top-left-radius: 8px;
        }}
        
        QHeaderView::section:last {{
            border-top-right-radius: 8px;
            border-right: none;
        }}
    """)
    
    # Additional table settings
    table.setAlternatingRowColors(True)
    table.verticalHeader().setVisible(False)
    table.setShowGrid(True)


def get_dashboard_card_style(color: str = None) -> str:
    """
    Get stylesheet for dashboard cards
    
    Args:
        color: Optional custom color for gradient
        
    Returns:
        QSS stylesheet string
    """
    base_color = color or AppConfig.PRIMARY_COLOR
    
    return f"""
        QFrame {{
            background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                stop:0 {base_color}22, stop:1 {base_color}44);
            border: 1px solid {base_color}44;
            border-radius: 12px;
            padding: 20px;
        }}
        
        QLabel {{
            color: white;
            border: none;
            background: transparent;
        }}
    """


def get_dialog_style() -> str:
    """Get stylesheet for modal dialogs"""
    return f"""
        QDialog {{
            background-color: {AppConfig.BACKGROUND_COLOR};
        }}
        
        QLabel {{
            color: {AppConfig.TEXT_COLOR};
        }}
        
        QPushButton {{
            background-color: {AppConfig.PRIMARY_COLOR};
            color: white;
            border: none;
            border-radius: 6px;
            padding: 10px 20px;
            font-weight: bold;
            min-width: 80px;
        }}
        
        QPushButton:hover {{
            background-color: {AppConfig.SECONDARY_COLOR};
        }}
    """


def get_product_card_style() -> str:
    """Get stylesheet for product cards"""
    return f"""
        QFrame#productCard {{
            background-color: {AppConfig.CARD_BACKGROUND};
            border: 1px solid #444;
            border-radius: 12px;
            padding: 15px;
        }}
        
        QFrame#productCard:hover {{
            border: 1px solid {AppConfig.PRIMARY_COLOR};
            background-color: #3A4A5A;
        }}
        
        QLabel {{
            color: {AppConfig.TEXT_COLOR};
            background: transparent;
        }}
        
        QPushButton {{
            background-color: {AppConfig.PRIMARY_COLOR};
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 12px;
            font-weight: bold;
        }}
        
        QPushButton:hover {{
            background-color: {AppConfig.SECONDARY_COLOR};
        }}
    """


def get_category_card_style() -> str:
    """Get stylesheet for category cards"""
    return f"""
        QFrame#categoryCard {{
            background-color: {AppConfig.CARD_BACKGROUND};
            border: 2px solid #555;
            border-radius: 10px;
            padding: 15px;
        }}
        
        QFrame#categoryCard:hover {{
            border: 2px solid {AppConfig.PRIMARY_COLOR};
        }}
    """


def show_error_message(title: str, message: str, parent=None):
    """
    Show a styled error message box
    
    Args:
        title: Dialog title
        message: Error message
        parent: Parent widget
    """
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Icon.Critical)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.setStyleSheet(f"""
        QMessageBox {{
            background-color: {AppConfig.BACKGROUND_COLOR};
        }}
        QLabel {{
            color: {AppConfig.TEXT_COLOR};
            min-width: 300px;
        }}
        QPushButton {{
            background-color: {AppConfig.ERROR_COLOR};
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 20px;
            font-weight: bold;
            min-width: 80px;
        }}
        QPushButton:hover {{
            background-color: #b02a2a;
        }}
    """)
    msg.exec()


def show_success_message(title: str, message: str, parent=None):
    """
    Show a styled success message box
    
    Args:
        title: Dialog title
        message: Success message
        parent: Parent widget
    """
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Icon.Information)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.setStyleSheet(f"""
        QMessageBox {{
            background-color: {AppConfig.BACKGROUND_COLOR};
        }}
        QLabel {{
            color: {AppConfig.TEXT_COLOR};
            min-width: 300px;
        }}
        QPushButton {{
            background-color: {AppConfig.SUCCESS_COLOR};
            color: white;
            border: none;
            border-radius: 6px;
            padding: 8px 20px;
            font-weight: bold;
            min-width: 80px;
        }}
        QPushButton:hover {{
            background-color: #009970;
        }}
    """)
    msg.exec()


def show_warning_message(title: str, message: str, parent=None):
    """
    Show a styled warning message box
    
    Args:
        title: Dialog title
        message: Warning message
        parent: Parent widget
    """
    msg = QMessageBox(parent)
    msg.setIcon(QMessageBox.Icon.Warning)
    msg.setWindowTitle(title)
    msg.setText(message)
    msg.setStyleSheet(f"""
        QMessageBox {{
            background-color: {AppConfig.BACKGROUND_COLOR};
        }}
        QLabel {{
            color: {AppConfig.TEXT_COLOR};
            min-width: 300px;
        }}
        QPushButton {{
            background-color: {AppConfig.WARNING_COLOR};
            color: #333;
            border: none;
            border-radius: 6px;
            padding: 8px 20px;
            font-weight: bold;
            min-width: 80px;
        }}
        QPushButton:hover {{
            background-color: #fcb942;
        }}
    """)
    msg.exec()