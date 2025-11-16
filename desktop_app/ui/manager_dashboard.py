"""  
Manager Dashboard for StockaDoodle  
Displays KPIs, sales trends, and category distribution charts  
"""  
  
from PyQt6.QtWidgets import (  
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,   
    QComboBox, QMessageBox, QSizePolicy  
)  
from PyQt6.QtCore import Qt  
from PyQt6.QtGui import QFont  
import logging  
  
# Matplotlib imports for charts  
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas  
from matplotlib.figure import Figure  
import matplotlib.pyplot as plt  
  
logger = logging.getLogger(__name__)  
  
  
class ManagerDashboardWidget(QWidget):  
    """Manager Dashboard with KPIs and Charts"""  
      
    def __init__(self, api_client, current_user, parent=None):  
        super().__init__(parent)  
        self.api = api_client  
        self.current_user = current_user  
          
        # Chart figures  
        self.sales_figure = None  
        self.category_figure = None  
        self.sales_canvas = None  
        self.category_canvas = None  
          
        self.init_ui()  
        self.load_dashboard_data()  
      
    def init_ui(self):  
        """Initialize the dashboard UI structure"""  
        main_layout = QVBoxLayout(self)  
        main_layout.setContentsMargins(20, 20, 20, 20)  
        main_layout.setSpacing(20)  
          
        # Title  
        title_label = QLabel("Manager Dashboard")  
        title_label.setStyleSheet("""  
            font-size: 24px;  
            font-weight: bold;  
            color: #2C3E50;  
            padding-bottom: 10px;  
        """)  
        main_layout.addWidget(title_label)  
          
        # KPI Cards Row  
        kpi_layout = QHBoxLayout()  
        kpi_layout.setSpacing(15)  
          
        self.revenue_card = self._create_kpi_card("Total Revenue", "$0.00", "#00B894")  
        self.sales_count_card = self._create_kpi_card("Total Sales", "0", "#6C5CE7")  
        self.transactions_card = self._create_kpi_card("Transactions", "0", "#74B9FF")  
          
        kpi_layout.addWidget(self.revenue_card)  
        kpi_layout.addWidget(self.sales_count_card)  
        kpi_layout.addWidget(self.transactions_card)  
          
        main_layout.addLayout(kpi_layout)  
          
        # Charts Container  
        charts_container = QWidget()  
        charts_layout = QHBoxLayout(charts_container)  
        charts_layout.setSpacing(15)  
        charts_layout.setContentsMargins(0, 0, 0, 0)  
          
        # Sales Trend Chart (60% width)  
        sales_chart_container = self._create_sales_chart_container()  
        charts_layout.addWidget(sales_chart_container, 6)  # 60% stretch  
          
        # Category Pie Chart (40% width)  
        category_chart_container = self._create_category_chart_container()  
        charts_layout.addWidget(category_chart_container, 4)  # 40% stretch  
          
        main_layout.addWidget(charts_container, 1)  # Stretch to fill remaining space  
      
    def _create_kpi_card(self, title: str, value: str, color: str) -> QFrame:  
        """Create a styled KPI card widget"""  
        card = QFrame()  
        card.setObjectName("kpi_card")  
        card.setStyleSheet(f"""  
            QFrame#kpi_card {{  
                background: qlineargradient(  
                    x1:0, y1:0, x2:0, y2:1,  
                    stop:0 {color},  
                    stop:1 {self._darken_color(color)}  
                );  
                border-radius: 10px;  
                padding: 20px;  
            }}  
        """)  
        card.setMinimumHeight(120)  
          
        layout = QVBoxLayout(card)  
        layout.setSpacing(10)  
          
        # Title  
        title_label = QLabel(title)  
        title_label.setStyleSheet("""  
            color: white;  
            font-size: 14px;  
            font-weight: 500;  
        """)  
        layout.addWidget(title_label)  
          
        # Value  
        value_label = QLabel(value)  
        value_label.setObjectName("kpi_value")  
        value_label.setStyleSheet("""  
            color: white;  
            font-size: 32px;  
            font-weight: bold;  
        """)  
        layout.addWidget(value_label)  
          
        layout.addStretch()  
          
        return card  
      
    def _darken_color(self, hex_color: str) -> str:  
        """Darken a hex color by 20% for gradient effect"""  
        hex_color = hex_color.lstrip('#')  
        r, g, b = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))  
        r = max(0, int(r * 0.8))  
        g = max(0, int(g * 0.8))  
        b = max(0, int(b * 0.8))  
        return f"#{r:02x}{g:02x}{b:02x}"  
      
    def _create_sales_chart_container(self) -> QFrame:  
        """Create container for sales trend bar chart"""  
        container = QFrame()  
        container.setStyleSheet("""  
            QFrame {  
                background-color: white;  
                border-radius: 10px;  
                border: 1px solid #E0E0E0;  
            }  
        """)  
          
        layout = QVBoxLayout(container)  
        layout.setContentsMargins(15, 15, 15, 15)  
        layout.setSpacing(10)  
          
        # Header with title and grouping selector  
        header_layout = QHBoxLayout()  
          
        title_label = QLabel("Sales Trend")  
        title_label.setStyleSheet("""  
            font-size: 16px;  
            font-weight: bold;  
            color: #2C3E50;  
        """)  
        header_layout.addWidget(title_label)  
          
        header_layout.addStretch()  
          
        # Grouping selector  
        grouping_label = QLabel("Group By:")  
        grouping_label.setStyleSheet("color: #7F8C8D; font-size: 12px;")  
        header_layout.addWidget(grouping_label)  
          
        self.grouping_combo = QComboBox()  
        self.grouping_combo.addItems(["Day", "Week", "Month"])  
        self.grouping_combo.setCurrentText("Day")  
        self.grouping_combo.currentTextChanged.connect(self.on_grouping_changed)  
        self.grouping_combo.setStyleSheet("""  
            QComboBox {  
                padding: 5px 10px;  
                border: 1px solid #BDC3C7;  
                border-radius: 5px;  
                background-color: white;  
            }  
        """)  
        header_layout.addWidget(self.grouping_combo)  
          
        layout.addLayout(header_layout)  
          
        # Chart canvas placeholder  
        self.sales_chart_frame = QFrame()  
        self.sales_chart_frame.setMinimumHeight(300)  
        self.sales_chart_layout = QVBoxLayout(self.sales_chart_frame)  
        self.sales_chart_layout.setContentsMargins(0, 0, 0, 0)  
          
        layout.addWidget(self.sales_chart_frame, 1)  
          
        return container  
      
    def _create_category_chart_container(self) -> QFrame:  
        """Create container for category pie chart"""  
        container = QFrame()  
        container.setStyleSheet("""  
            QFrame {  
                background-color: white;  
                border-radius: 10px;  
                border: 1px solid #E0E0E0;  
            }  
        """)  
          
        layout = QVBoxLayout(container)  
        layout.setContentsMargins(15, 15, 15, 15)  
        layout.setSpacing(10)  
          
        # Title  
        title_label = QLabel("Product Distribution")  
        title_label.setStyleSheet("""  
            font-size: 16px;  
            font-weight: bold;  
            color: #2C3E50;  
        """)  
        layout.addWidget(title_label)  
          
        # Chart canvas placeholder  
        self.category_chart_frame = QFrame()  
        self.category_chart_frame.setMinimumHeight(300)  
        self.category_chart_layout = QVBoxLayout(self.category_chart_frame)  
        self.category_chart_layout.setContentsMargins(0, 0, 0, 0)  
          
        layout.addWidget(self.category_chart_frame, 1)  
          
        return container  
      
    def _update_kpi_card(self, card: QFrame, value: str):  
        """Update KPI card value"""  
        value_label = card.findChild(QLabel, "kpi_value")  
        if value_label:  
            value_label.setText(value)  
      
    def load_dashboard_data(self):  
        """Load all dashboard data from API"""  
        self.load_kpi_data()  
        self.load_sales_chart()  
        self.load_category_chart()  
      
    def load_kpi_data(self):  
        """Load KPI summary data"""  
        try:  
            resp = self.api.reports.get_sales_summary()  
              
            if resp.success:  
                data = resp.data  
                  
                # Update KPI cards  
                revenue = data.get('total_revenue', 0.0)  
                sales_count = data.get('total_sales', 0)  
                transactions = data.get('total_transactions', 0)  
                  
                self._update_kpi_card(self.revenue_card, f"${revenue:,.2f}")  
                self._update_kpi_card(self.sales_count_card, f"{sales_count:,}")  
                self._update_kpi_card(self.transactions_card, f"{transactions:,}")  
                  
                logger.info("KPI data loaded successfully")  
            else:  
                logger.error(f"Failed to load KPI data: {resp.error}")  
                QMessageBox.warning(self, "Data Load Error",   
                                  f"Could not load KPI data: {resp.error}")  
        except Exception as e:  
            logger.error(f"Exception loading KPI data: {e}", exc_info=True)  
            QMessageBox.critical(self, "Error", f"Failed to load KPI data: {str(e)}")  
      
    def on_grouping_changed(self, grouping: str):  
        """Handle grouping combo box change"""  
        self.load_sales_chart()  
      
    def load_sales_chart(self):  
        """Load and render sales trend bar chart"""  
        try:  
            grouping = self.grouping_combo.currentText().lower()  
            resp = self.api.reports.get_sales_by_time(grouping)  
              
            if resp.success:  
                data = resp.data  
                  
                # Clear existing chart  
                if self.sales_canvas:  
                    self.sales_chart_layout.removeWidget(self.sales_canvas)  
                    self.sales_canvas.deleteLater()  
                    self.sales_canvas = None  
                  
                # Create new figure and canvas  
                self.sales_figure = Figure(figsize=(8, 4), dpi=100)  
                self.sales_canvas = FigureCanvas(self.sales_figure)  
                self.sales_chart_layout.addWidget(self.sales_canvas)  
                  
                # Plot data  
                ax = self.sales_figure.add_subplot(111)  
                  
                if data and len(data) > 0:  
                    periods = [item['period'] for item in data]  
                    sales = [item['total_sales'] for item in data]  
                      
                    ax.bar(periods, sales, color='#6C5CE7', alpha=0.8)  
                    ax.set_xlabel(f'{grouping.capitalize()}', fontsize=10)  
                    ax.set_ylabel('Total Sales ($)', fontsize=10)  
                    ax.tick_params(axis='x', rotation=45, labelsize=8)  
                    ax.tick_params(axis='y', labelsize=8)  
                    ax.grid(axis='y', alpha=0.3)  
                else:  
                    ax.text(0.5, 0.5, 'No sales data available',   
                           ha='center', va='center', fontsize=12, color='#7F8C8D')  
                    ax.set_xticks([])  
                    ax.set_yticks([])  
                  
                self.sales_figure.tight_layout()  
                self.sales_canvas.draw()  
                  
                logger.info(f"Sales chart loaded for grouping: {grouping}")  
            else:  
                logger.error(f"Failed to load sales chart: {resp.error}")  
        except Exception as e:  
            logger.error(f"Exception loading sales chart: {e}", exc_info=True)  
      
    def load_category_chart(self):  
        """Load and render category distribution pie chart"""  
        try:  
            resp = self.api.reports.get_category_product_counts()  
              
            if resp.success:  
                data = resp.data  
                  
                # Clear existing chart  
                if self.category_canvas:  
                    self.category_chart_layout.removeWidget(self.category_canvas)  
                    self.category_canvas.deleteLater()  
                    self.category_canvas = None  
                  
                # Create new figure and canvas  
                self.category_figure = Figure(figsize=(4, 4), dpi=100)  
                self.category_canvas = FigureCanvas(self.category_figure)  
                self.category_chart_layout.addWidget(self.category_canvas)  
                  
                # Plot data  
                ax = self.category_figure.add_subplot(111)  
                  
                if data and len(data) > 0:  
                    categories = [item['category_name'] for item in data]  
                    counts = [item['product_count'] for item in data]  
                      
                    colors = ['#6C5CE7', '#00B894', '#74B9FF', '#FDCB6E', '#D63031']  
                    ax.pie(counts, labels=categories, autopct='%1.1f%%',   
                          colors=colors[:len(categories)], startangle=90)  
                    ax.axis('equal')  
                else:  
                    ax.text(0.5, 0.5,   