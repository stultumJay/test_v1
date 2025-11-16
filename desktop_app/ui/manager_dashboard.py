from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFrame, QLabel, QComboBox, QMessageBox, 
    QSizePolicy, QPushButton
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QColor

# Matplotlib dependencies for charting
import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from utils.config import AppConfig, CURRENT_SESSION
from utils.decorators import role_required
from utils.style_utils import create_kpi_card

class ChartWidget(QWidget):
    """A generic widget to hold a Matplotlib chart canvas."""
    def __init__(self, parent=None):
        super().__init__(parent)
        self.figure = Figure(figsize=(5, 4), dpi=100)
        self.figure.patch.set_facecolor(AppConfig.DARK_SECONDARY_COLOR)
        self.canvas = FigureCanvas(self.figure)
        
        # Set background for the canvas to match the widget
        self.canvas.setStyleSheet(f"background-color: {AppConfig.DARK_SECONDARY_COLOR}; border-radius: 8px;")
        
        layout = QVBoxLayout(self)
        layout.addWidget(self.canvas)
        self.setLayout(layout)
        
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)


class ManagerDashboardWidget(QWidget):
    """
    Dashboard for Managers: Displays key performance indicators and sales charts.
    """
    
    def __init__(self, api_client, current_user, parent=None):
        super().__init__(parent)
        self.api = api_client
        self.current_user = current_user
        self.sales_summary = {}
        self.sales_data = [] # For bar chart
        self.category_data = [] # For pie chart
        
        self.init_ui()
        # Use QTimer to ensure UI is ready before first data load
        QTimer.singleShot(10, self.load_all_data)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        # 1. Header
        header = QLabel(f"Manager Dashboard - {self.current_user['username']}")
        header.setFont(QFont(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_TITLE, QFont.Weight.Bold))
        header.setStyleSheet("color: white;")
        main_layout.addWidget(header)
        
        # 2. KPI Cards (Top Row)
        self.kpi_layout = QHBoxLayout()
        self.kpi_layout.setSpacing(15)
        
        # Initialize placeholders for KPI cards
        self.revenue_card = create_kpi_card("Total Revenue", "$0.00", AppConfig.ICON_DOLLAR, AppConfig.COLOR_GREEN)
        self.sales_card = create_kpi_card("Total Sales", "0", AppConfig.ICON_SALES_TAG, AppConfig.COLOR_BLUE)
        self.transactions_card = create_kpi_card("Total Transactions", "0", AppConfig.ICON_TRANSACTIONS, AppConfig.COLOR_ORANGE)
        
        self.kpi_layout.addWidget(self.revenue_card)
        self.kpi_layout.addWidget(self.sales_card)
        self.kpi_layout.addWidget(self.transactions_card)
        self.kpi_layout.addStretch(1)
        
        main_layout.addLayout(self.kpi_layout)

        # 3. Charts Container (Bar Chart and Pie Chart)
        chart_container = QWidget()
        chart_container.setStyleSheet(f"background-color: {AppConfig.DARK_SECONDARY_COLOR}; border-radius: 12px; padding: 15px;")
        chart_layout = QHBoxLayout(chart_container)
        chart_layout.setSpacing(20)
        
        # 3a. Sales Trend Bar Chart (65% width)
        self.sales_chart_widget = QWidget()
        sales_chart_layout = QVBoxLayout(self.sales_chart_widget)
        
        # Bar Chart Controls
        control_frame = QFrame()
        control_layout = QHBoxLayout(control_frame)
        control_layout.setContentsMargins(0, 0, 0, 0)
        
        label_grouping = QLabel("Sales Trend Grouping:")
        label_grouping.setStyleSheet("color: #A0A0A0; font-weight: bold;")
        
        self.grouping_combo = QComboBox()
        self.grouping_combo.addItems(["Day", "Week", "Month"])
        self.grouping_combo.setCurrentText("Month") # Default to Monthly view
        self.grouping_combo.currentTextChanged.connect(self.load_sales_by_time)
        self.grouping_combo.setStyleSheet(AppConfig.COMBOBOX_STYLE)
        
        control_layout.addWidget(label_grouping)
        control_layout.addWidget(self.grouping_combo)
        control_layout.addStretch(1)
        
        sales_chart_layout.addWidget(control_frame)
        
        # Matplotlib Canvas for Bar Chart
        self.bar_chart = ChartWidget()
        sales_chart_layout.addWidget(self.bar_chart)
        
        self.sales_chart_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        self.sales_chart_widget.setMinimumWidth(400) # Ensure it has enough room
        chart_layout.addWidget(self.sales_chart_widget, 65) # 65% weight

        # 3b. Category Distribution Pie Chart (35% width)
        self.category_chart_widget = QWidget()
        category_chart_layout = QVBoxLayout(self.category_chart_widget)
        
        # Title
        cat_title = QLabel("Product Distribution by Category")
        cat_title.setFont(QFont(AppConfig.FONT_FAMILY, AppConfig.FONT_SIZE_NORMAL + 1, QFont.Weight.Bold))
        cat_title.setStyleSheet("color: white;")
        cat_title.setAlignment(AppConfig.ALIGN_CENTER)
        category_chart_layout.addWidget(cat_title)
        
        # Matplotlib Canvas for Pie Chart
        self.pie_chart = ChartWidget()
        category_chart_layout.addWidget(self.pie_chart)
        
        self.category_chart_widget.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)
        chart_layout.addWidget(self.category_chart_widget, 35) # 35% weight
        
        main_layout.addWidget(chart_container)
        main_layout.addStretch(1)

    def load_all_data(self):
        """Loads all data required for the dashboard."""
        self.load_sales_summary()
        self.load_category_product_counts()
        self.load_sales_by_time() # This uses the default grouping from the combo box

    def load_sales_summary(self):
        """Fetches and updates KPI cards."""
        resp = self.api.reports.get_sales_summary()
        if resp.success:
            data = resp.data
            
            # Find the labels in the card widgets and update their values
            # Revenue card (index 1 is the value label in the text container)
            self.revenue_card.findChild(QVBoxLayout).itemAt(1).widget().setText(
                f"${data.get('total_revenue', 0.0):,.2f}"
            )
            # Sales card
            self.sales_card.findChild(QVBoxLayout).itemAt(1).widget().setText(
                f"{data.get('total_sales', 0):,}"
            )
            # Transactions card
            self.transactions_card.findChild(QVBoxLayout).itemAt(1).widget().setText(
                f"{data.get('transaction_count', 0):,}"
            )
        else:
            QMessageBox.warning(self, "API Error", f"Failed to load sales summary: {resp.message}")

    def load_category_product_counts(self):
        """Fetches data and draws the Pie Chart."""
        resp = self.api.reports.get_category_product_counts()
        if resp.success:
            self.category_data = resp.data
            self.draw_pie_chart()
        else:
            QMessageBox.warning(self, "API Error", f"Failed to load category data: {resp.message}")

    def load_sales_by_time(self):
        """Fetches data based on grouping and draws the Bar Chart."""
        grouping = self.grouping_combo.currentText().lower()
        resp = self.api.reports.get_sales_by_time(grouping)
        if resp.success:
            self.sales_data = resp.data
            self.draw_bar_chart(grouping)
        else:
            QMessageBox.warning(self, "API Error", f"Failed to load sales trend: {resp.message}")

    def draw_bar_chart(self, grouping: str):
        """Renders the sales trend data on the bar chart canvas."""
        fig = self.bar_chart.figure
        fig.clear()
        
        ax = fig.add_subplot(111)
        ax.set_facecolor(AppConfig.DARK_SECONDARY_COLOR)
        
        dates = [item['period'] for item in self.sales_data]
        sales = [item['total_sales'] for item in self.sales_data]
        
        if not sales:
            ax.text(0.5, 0.5, "No sales data available for this period.", 
                    color='white', ha='center', va='center', transform=ax.transAxes)
        else:
            ax.bar(dates, sales, color=AppConfig.PRIMARY_COLOR, alpha=0.8, zorder=3)
            ax.set_title(f"Sales Trend ({grouping.title()} View)", color='white')
            ax.set_xlabel(f"{grouping.title()} Period", color='#A0A0A0')
            ax.set_ylabel("Total Sales ($)", color='#A0A0A0')
            
            # Style axes
            ax.tick_params(axis='x', colors='#A0A0A0', rotation=45, labelsize=8)
            ax.tick_params(axis='y', colors='#A0A0A0')
            ax.spines['bottom'].set_color('#303030')
            ax.spines['left'].set_color('#303030')
            ax.spines['top'].set_visible(False)
            ax.spines['right'].set_visible(False)
            ax.grid(axis='y', linestyle='--', alpha=0.3, color='#303030')
            fig.tight_layout()

        self.bar_chart.canvas.draw()

    def draw_pie_chart(self):
        """Renders the category distribution data on the pie chart canvas."""
        fig = self.pie_chart.figure
        fig.clear()
        
        ax = fig.add_subplot(111)
        ax.set_facecolor(AppConfig.DARK_SECONDARY_COLOR)
        
        labels = [item['category_name'] for item in self.category_data]
        sizes = [item['product_count'] for item in self.category_data]
        
        if not sizes or sum(sizes) == 0:
            ax.text(0.5, 0.5, "No product category data available.", 
                    color='white', ha='center', va='center', transform=ax.transAxes)
        else:
            # Use distinct colors
            colors = ['#8C7AE6', '#00B894', '#FF7F50', '#0984E3', '#FABE2C', '#D63031']
            
            ax.pie(
                sizes, 
                labels=labels, 
                autopct='%1.1f%%', 
                startangle=90, 
                colors=colors[:len(labels)],
                textprops={'color': 'white', 'fontsize': 9}
            )
            ax.axis('equal')  # Equal aspect ratio ensures that pie is drawn as a circle.
            ax.set_title("Product Category Distribution", color='white')
        
        self.pie_chart.canvas.draw()