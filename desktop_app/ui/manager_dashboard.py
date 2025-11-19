"""
Manager Dashboard - Analytics & Inventory Alerts
Features charts, KPIs, and real-time inventory warnings
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QComboBox,
    QTableWidget, QTableWidgetItem, QFrame, QHeaderView
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from api_client.stockadoodle_api import StockaDoodleAPI
from utils.config import AppConfig
from utils.decorators import role_required
from utils.styles import apply_table_styles


class MplCanvas(FigureCanvas):
    """Matplotlib canvas for embedding plots"""
    def __init__(self, parent=None, width=6, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        fig.patch.set_facecolor(AppConfig.CARD_BACKGROUND)
        self.axes = fig.add_subplot(111)
        self.axes.set_facecolor(AppConfig.CARD_BACKGROUND)
        super().__init__(fig)


class ManagerDashboardWidget(QWidget):
    """Manager Dashboard with Analytics Focus"""
    
    def __init__(self, api_client: StockaDoodleAPI, parent=None):
        super().__init__(parent)
        self.api = api_client
        
        self.setStyleSheet(f"background-color: {AppConfig.BACKGROUND_COLOR};")
        self.init_ui()
        
        # Load data asynchronously
        QTimer.singleShot(100, self.load_dashboard_data)
        
    def init_ui(self):
        """Initialize the UI layout"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(20)
        
        # Header
        header = QLabel("Manager Dashboard - Analytics & Alerts")
        header.setFont(QFont(AppConfig.FONT_FAMILY, 24, QFont.Weight.Bold))
        header.setStyleSheet("color: white; margin-bottom: 10px;")
        main_layout.addWidget(header)
        
        # KPI Cards Row
        kpi_layout = self._create_kpi_section()
        main_layout.addLayout(kpi_layout)
        
        # Charts Section
        charts_layout = self._create_charts_section()
        main_layout.addLayout(charts_layout)
        
        # Alerts Section
        alerts_section = self._create_alerts_section()
        main_layout.addWidget(alerts_section)
        
        main_layout.addStretch()
        
    def _create_kpi_section(self) -> QHBoxLayout:
        """Create KPI cards"""
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(15)
        
        # KPI Cards
        cards_data = [
            ("Total Revenue", "0.00", "dollar-sign", "#00B894"),
            ("Today's Sales", "0", "shopping-cart", "#6C5CE7"),
            ("Low Stock Items", "0", "alert-triangle", "#FDCB6E"),
            ("Expiring Soon", "0", "calendar", "#D63031"),
        ]
        
        self.kpi_labels = {}
        
        for title, default_val, icon, color in cards_data:
            card = self._create_kpi_card(title, default_val, color)
            self.kpi_labels[title] = card.findChild(QLabel, "value")
            kpi_layout.addWidget(card)
            
        return kpi_layout
        
    def _create_kpi_card(self, title: str, value: str, color: str) -> QFrame:
        """Create a single KPI card"""
        card = QFrame()
        card.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1,
                    stop:0 {color}22, stop:1 {color}44);
                border: 1px solid {color}44;
                border-radius: 10px;
                padding: 15px;
                min-height: 100px;
            }}
        """)
        
        layout = QVBoxLayout(card)
        
        title_label = QLabel(title)
        title_label.setStyleSheet("color: #ccc; font-size: 10pt;")
        layout.addWidget(title_label)
        
        value_label = QLabel(value)
        value_label.setObjectName("value")
        value_label.setStyleSheet("color: white; font-size: 24pt; font-weight: bold;")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(value_label)
        
        return card
        
    def _create_charts_section(self) -> QHBoxLayout:
        """Create charts section with bar chart and pie chart"""
        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(20)
        
        # Left: Bar Chart
        bar_section = QFrame()
        bar_section.setStyleSheet(f"""
            QFrame {{
                background-color: {AppConfig.CARD_BACKGROUND};
                border-radius: 12px;
                padding: 15px;
            }}
        """)
        
        bar_layout = QVBoxLayout(bar_section)
        
        # Chart controls
        control_layout = QHBoxLayout()
        control_layout.addWidget(QLabel("Sales Trend - View by:"))
        
        self.grouping_combo = QComboBox()
        self.grouping_combo.addItems(["Daily", "Weekly", "Monthly"])
        self.grouping_combo.setCurrentText("Monthly")
        self.grouping_combo.currentTextChanged.connect(self.refresh_bar_chart)
        control_layout.addWidget(self.grouping_combo)
        control_layout.addStretch()
        
        bar_layout.addLayout(control_layout)
        
        # Bar chart canvas
        self.bar_canvas = MplCanvas(self, width=6, height=4)
        bar_layout.addWidget(self.bar_canvas)
        
        charts_layout.addWidget(bar_section, 60)
        
        # Right: Pie Chart
        pie_section = QFrame()
        pie_section.setStyleSheet(f"""
            QFrame {{
                background-color: {AppConfig.CARD_BACKGROUND};
                border-radius: 12px;
                padding: 15px;
            }}
        """)
        
        pie_layout = QVBoxLayout(pie_section)
        
        pie_title = QLabel("Inventory by Category")
        pie_title.setStyleSheet("color: white; font-weight: bold; font-size: 12pt;")
        pie_layout.addWidget(pie_title)
        
        self.pie_canvas = MplCanvas(self, width=4, height=4)
        pie_layout.addWidget(self.pie_canvas)
        
        charts_layout.addWidget(pie_section, 40)
        
        return charts_layout
        
    def _create_alerts_section(self) -> QFrame:
        """Create low stock alerts table"""
        section = QFrame()
        section.setStyleSheet(f"""
            QFrame {{
                background-color: {AppConfig.CARD_BACKGROUND};
                border-radius: 12px;
                padding: 20px;
            }}
        """)
        
        layout = QVBoxLayout(section)
        
        title = QLabel("⚠️ Critical Low Stock Items")
        title.setFont(QFont(AppConfig.FONT_FAMILY, 14, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {AppConfig.WARNING_COLOR};")
        layout.addWidget(title)
        
        self.alerts_table = QTableWidget(0, 4)
        self.alerts_table.setHorizontalHeaderLabels(
            ["Product", "Brand", "Current Stock", "Min Level"]
        )
        apply_table_styles(self.alerts_table)
        
        header = self.alerts_table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.Stretch)
        
        self.alerts_table.setMaximumHeight(250)
        layout.addWidget(self.alerts_table)
        
        return section
        
    @role_required('Admin', 'Manager')
    def load_dashboard_data(self):
        """Load all dashboard data from API"""
        try:
            # Fetch manager metrics
            metrics_resp = self.api.dashboard.manager()
            
            if metrics_resp.success:
                data = metrics_resp.data
                
                # Update KPIs
                self.kpi_labels["Low Stock Items"].setText(
                    str(data.get('low_stock_count', 0))
                )
                self.kpi_labels["Expiring Soon"].setText(
                    str(data.get('expiring_count', 0))
                )
            
            # Fetch sales summary
            sales_resp = self.api.reports.get_sales_summary()
            if sales_resp.success:
                sales_data = sales_resp.data
                revenue = sales_data.get('total_revenue', 0)
                self.kpi_labels["Total Revenue"].setText(f"${revenue:,.2f}")
                self.kpi_labels["Today's Sales"].setText(
                    str(sales_data.get('total_sales_count', 0))
                )
            
            # Load charts
            self.refresh_bar_chart()
            self.refresh_pie_chart()
            
            # Load alerts
            self.load_low_stock_alerts()
            
        except Exception as e:
            print(f"Error loading manager dashboard: {e}")
            
    def refresh_bar_chart(self):
        """Refresh the sales trend bar chart"""
        grouping = self.grouping_combo.currentText().lower()
        
        try:
            resp = self.api.reports.get_sales_by_time(grouping=grouping)
            
            if resp.success:
                data = resp.data
                
                ax = self.bar_canvas.axes
                ax.clear()
                
                if not data:
                    ax.text(0.5, 0.5, "No sales data available",
                           transform=ax.transAxes, ha='center', va='center',
                           color='#888', fontsize=12)
                else:
                    periods = [item['period'] for item in data]
                    amounts = [item['total_revenue'] for item in data]
                    
                    bars = ax.bar(periods, amounts, color='#6C5CE7',
                                 edgecolor='#5a4dbf', linewidth=1.2)
                    
                    ax.set_title(f"Sales Trend - {grouping.title()} View",
                               color='white', fontsize=12, pad=15)
                    ax.set_ylabel("Revenue ($)", color='#aaa')
                    ax.tick_params(colors='#aaa', labelsize=9)
                    ax.grid(axis='y', alpha=0.2, linestyle='--')
                    
                    # Rotate x-axis labels if daily
                    if grouping == 'daily':
                        import matplotlib.pyplot as plt
                        plt.setp(ax.get_xticklabels(), rotation=45, ha='right')
                    
                ax.spines['top'].set_visible(False)
                ax.spines['right'].set_visible(False)
                ax.spines['left'].set_color('#555')
                ax.spines['bottom'].set_color('#555')
                
                self.bar_canvas.draw()
                
        except Exception as e:
            print(f"Error refreshing bar chart: {e}")
            
    def refresh_pie_chart(self):
        """Refresh the category distribution pie chart"""
        try:
            resp = self.api.reports.get_category_product_counts()
            
            if resp.success:
                data = resp.data
                
                ax = self.pie_canvas.axes
                ax.clear()
                
                if not data:
                    ax.text(0.5, 0.5, "No product data",
                           transform=ax.transAxes, ha='center', va='center',
                           color='#888')
                else:
                    categories = [item['category_name'] for item in data]
                    counts = [item['product_count'] for item in data]
                    
                    colors = ['#6C5CE7', '#00B894', '#D63031', '#FDCB6E', '#74B9FF', '#A29BFE']
                    
                    wedges, texts, autotexts = ax.pie(
                        counts,
                        labels=categories,
                        autopct='%1.1f%%',
                        startangle=90,
                        colors=colors[:len(categories)],
                        textprops={'color': 'white', 'weight': 'bold'},
                        wedgeprops={'edgecolor': '#333'}
                    )
                    
                    for autotext in autotexts:
                        autotext.set_color('white')
                        autotext.set_fontsize(9)
                        
                ax.set_title("Product Distribution", color='white', fontsize=12, pad=15)
                self.pie_canvas.draw()
                
        except Exception as e:
            print(f"Error refreshing pie chart: {e}")
            
    def load_low_stock_alerts(self):
        """Load low stock items into alerts table"""
        try:
            resp = self.api.products_enhanced.get_low_stock()
            
            if resp.success:
                products = resp.data
                
                self.alerts_table.setRowCount(0)
                
                for product in products[:20]:  # Limit to 20
                    row = self.alerts_table.rowCount()
                    self.alerts_table.insertRow(row)
                    
                    self.alerts_table.setItem(row, 0,
                        QTableWidgetItem(product.get('name', 'N/A')))
                    self.alerts_table.setItem(row, 1,
                        QTableWidgetItem(product.get('brand', 'N/A')))
                    self.alerts_table.setItem(row, 2,
                        QTableWidgetItem(str(product.get('stock_level', 0))))
                    self.alerts_table.setItem(row, 3,
                        QTableWidgetItem(str(product.get('min_stock_level', 0))))
                        
        except Exception as e:
            print(f"Error loading alerts: {e}")