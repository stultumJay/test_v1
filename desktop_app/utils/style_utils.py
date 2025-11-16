from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QHBoxLayout, QFrame
from PyQt6.QtGui import QFont
from utils.config import AppConfig

def create_kpi_card(title: str, value: Union[str, float, int], icon_code: str, primary_color: str) -> QWidget:
    """
    Creates a standardized, styled Key Performance Indicator (KPI) card.
    
    Args:
        title: The title of the metric (e.g., 'Total Revenue').
        value: The value of the metric (e.g., 12345.67).
        icon_code: A FontAwesome icon code (e.g., '\uf51e').
        primary_color: The color used for the icon background (e.g., '#00B894').
        
    Returns:
        A QWidget representing the complete KPI card.
    """
    card = QFrame()
    card.setFixedSize(220, 100)
    card.setStyleSheet(f"""
        QFrame {{
            background-color: {AppConfig.DARK_SECONDARY_COLOR};
            border: 1px solid rgba(255, 255, 255, 0.1);
            border-radius: 12px;
            padding: 10px;
        }}
    """)
    
    # Main layout (Horizontal: Icon + Text)
    main_layout = QHBoxLayout(card)
    main_layout.setContentsMargins(10, 10, 10, 10)
    main_layout.setSpacing(15)

    # 1. Icon Container
    icon_container = QWidget()
    icon_container.setFixedSize(60, 60)
    icon_container.setStyleSheet(f"""
        QWidget {{
            background-color: {primary_color};
            border-radius: 8px;
        }}
    """)
    icon_layout = QHBoxLayout(icon_container)
    icon_layout.setContentsMargins(0, 0, 0, 0)
    
    icon_label = QLabel(icon_code)
    icon_label.setFont(QFont(AppConfig.FONT_FAMILY_ICONS, 20))
    icon_label.setStyleSheet("color: white;")
    icon_label.setAlignment(AppConfig.ALIGN_CENTER)
    icon_layout.addWidget(icon_label)
    
    main_layout.addWidget(icon_container)

    # 2. Text Content (Title and Value)
    text_container = QVBoxLayout()
    text_container.setSpacing(5)
    
    # Title Label
    title_label = QLabel(title)
    title_label.setFont(QFont(AppConfig.FONT_FAMILY, 9))
    title_label.setStyleSheet("color: #A0A0A0;")
    text_container.addWidget(title_label)
    
    # Value Label
    value_label = QLabel(str(value))
    value_label.setFont(QFont(AppConfig.FONT_FAMILY, 18, QFont.Weight.Bold))
    value_label.setStyleSheet("color: white;")
    value_label.setTextElideMode(AppConfig.ELIDE_MIDDLE)
    text_container.addWidget(value_label)
    
    main_layout.addLayout(text_container)
    main_layout.addStretch(1)

    return card

# Helper function for setting up table widgets (assuming it exists in original LogiJex)
# For this purpose, we'll ensure a minimal style utility function is available.

def setup_standard_table(table_widget):
    """Applies standard StockaDoodle styling to a QTableWidget."""
    # Placeholder for a much more detailed styling function
    table_widget.setAlternatingRowColors(True)
    table_widget.setStyleSheet(f"""
        QTableWidget {{
            background-color: {AppConfig.DARK_SECONDARY_COLOR};
            color: white;
            gridline-color: rgba(255, 255, 255, 0.1);
            border-radius: 8px;
        }}
        QHeaderView::section {{
            background-color: {AppConfig.PRIMARY_COLOR};
            color: white;
            border: none;
            padding: 5px;
        }}
        QTableWidget::item:selected {{
            background-color: {AppConfig.ACCENT_COLOR};
            color: white;
        }}
    """)

# The full style_utils.py would contain all icon codes and table styling logic.
# The KPI card function is the key addition for the dashboards.