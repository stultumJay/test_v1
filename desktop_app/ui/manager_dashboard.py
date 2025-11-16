"""
manager_dashboard.py
Modern Analytics-First Manager Dashboard
Features:
- KPI Cards (Revenue, Sales, Transactions)
- Interactive Sales Trend Bar Chart (Day/Week/Month)
- Product Category Distribution Pie Chart
- Low Stock Alert Table
- Expiring Items Alert Table
- Clean, dark-themed, responsive layout
"""

from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QComboBox,
    QGroupBox, QScrollArea, QTableWidget, QTableWidgetItem, QSizePolicy
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont, QPixmap

import matplotlib
matplotlib.use('QtAgg')
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure

from ui.dashboard_widgets import BadgeLabel, apply_table_styles
from utils.config import AppConfig
from core.product_manager import ProductManager
from core.sales_manager import SalesManager
from core.activity_logger import ActivityLogger


class MplCanvas(FigureCanvas):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        fig = Figure(figsize=(width, height), dpi=dpi)
        fig.patch.set_facecolor('#1e1e1e')
        self.axes = fig.add_subplot(111)
        self.axes.set_facecolor('#1e1e1e')
        super().__init__(fig)


class ManagerDashboard(QWidget):
    def __init__(self, current_user: dict, parent=None):
        super().__init__(parent)
        self.current_user = current_user
        self.product_manager = ProductManager()
        self.sales_manager = SalesManager()
        self.activity_logger = ActivityLogger()

        self.setStyleSheet("background-color: #121212; color: white;")
        self.init_ui()
        QTimer.singleShot(100, self.load_all_data)

    def init_ui(self):
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(25, 25, 25, 25)
        main_layout.setSpacing(25)

        # Header
        header = QLabel("Manager Dashboard")
        header.setFont(QFont(AppConfig.FONT_FAMILY, 28, QFont.Weight.Bold))
        header.setStyleSheet("color: #ffffff; padding: 10px;")
        header.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(header)

        # KPI Row
        kpi_layout = QHBoxLayout()
        kpi_layout.setSpacing(20)
        self.kpi_cards = [
            self.create_kpi_card("Total Revenue", "$0.00", "💰", "#4caf50"),
            self.create_kpi_card("Today's Sales", "$0.00", "🛒", "#2196f3"),
            self.create_kpi_card("Active Products", "0", "📦", "#ff9800"),
            self.create_kpi_card("Low Stock Items", "0", "⚠️", "#f44336")
        ]
        for card in self.kpi_cards:
            kpi_layout.addWidget(card)
        main_layout.addLayout(kpi_layout)

        # Charts Row
        charts_row = QHBoxLayout()
        charts_row.setSpacing(25)

        # Left: Sales Trend Bar Chart
        bar_container = QGroupBox("Sales Trend Over Time")
        bar_container.setStyleSheet(self.get_chart_group_style())
        bar_layout = QVBoxLayout(bar_container)

        control_layout = QHBoxLayout()
        control_layout.addWidget(QLabel("View by:"))
        self.grouping_combo = QComboBox()
        self.grouping_combo.addItems(["Daily", "Weekly", "Monthly"])
        self.grouping_combo.setCurrentText("Monthly")
        self.grouping_combo.currentTextChanged.connect(self.refresh_sales_chart)
        control_layout.addWidget(self.grouping_combo)
        control_layout.addStretch()
        bar_layout.addLayout(control_layout)

        self.bar_canvas = MplCanvas(self, width=6, height=4.5)
        bar_layout.addWidget(self.bar_canvas)
        charts_row.addWidget(bar_container, 6)

        # Right: Category Pie Chart
        pie_container = QGroupBox("Product Distribution by Category")
        pie_container.setStyleSheet(self.get_chart_group_style())
        pie_layout = QVBoxLayout(pie_container)
        self.pie_canvas = MplCanvas(self, width=5, height=5)
        pie_layout.addWidget(self.pie_canvas)
        charts_row.addWidget(pie_container, 4)

        main_layout.addLayout(charts_row)

        # Alerts Section
        alerts_layout = QHBoxLayout()
        alerts_layout.setSpacing(25)

        # Low Stock Table
        low_stock_box = QGroupBox("Low Stock Alerts")
        low_stock_box.setStyleSheet(self.get_alert_box_style())
        low_layout = QVBoxLayout(low_stock_box)
        self.low_stock_table = QTableWidget(0, 4)
        self.low_stock_table.setHorizontalHeaderLabels(["Product", "Current", "Min Level", "Status"])
        apply_table_styles(self.low_stock_table)
        self.low_stock_table.horizontalHeader().setStretchLastSection(True)
        low_layout.addWidget(self.low_stock_table)
        alerts_layout.addWidget(low_stock_box)

        # Expiring Items (Future-Proof)
        expiring_box = QGroupBox("Expiring Soon (Next 30 Days)")
        expiring_box.setStyleSheet(self.get_alert_box_style())
        exp_layout = QVBoxLayout(expiring_box)
        self.expiring_table = QTableWidget(0, 4)
        self.expiring_table.setHorizontalHeaderLabels(["Product", "Batch", "Expiry Date", "Days Left"])
        apply_table_styles(self.expiring_table)
        self.expiring_table.horizontalHeader().setStretchLastSection(True)
        exp_layout.addWidget(self.expiring_table)
        alerts_layout.addWidget(expiring_box)

        main_layout.addLayout(alerts_layout)
        main_layout.addStretch()

    def get_chart_group_style(self):
        return """
            QGroupBox {
                background-color: #1e1e1e;
                border: 1px solid #333;
                border-radius: 12px;
                padding: 15px;
                font-weight: bold;
                color: white;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 15px;
                padding: 0 10px;
                background: #1e1e1e;
            }
        """

    def get_alert_box_style(self):
        return """
            QGroupBox {
                background-color: #1e1e1e;
                border: 1px solid #444;
                border-radius: 12px;
                padding: 10px;
                font-weight: bold;
                color: #ff9800;
            }
            QGroupBox::title {
                color: #ff9800;
                background: #1e1e1e;
                padding: 5px 15px;
            }
        """

    def create_kpi_card(self, title: str, value: str, icon: str, color: str):
        frame = QFrame()
        frame.setStyleSheet(f"""
            QFrame {{
                background: qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 {color}22, stop:1 {color}44);
                border: 1px solid {color}44;
                border-radius: 16px;
                padding: 20px;
            }}
        """)
        frame.setFixedHeight(130)
        layout = QVBoxLayout(frame)
        layout.setSpacing(10)

        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Segoe UI Emoji", 32))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        title_label = QLabel(title)
        title_label.setStyleSheet("font-size: 13pt; color: #ccc;")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        value_label = QLabel(value)
        value_label.setStyleSheet(f"font-size: 24pt; font-weight: bold; color: white;")
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        layout.addWidget(icon_label)
        layout.addWidget(title_label)
        layout.addWidget(value_label)
        return frame

    def load_all_data(self):
        self.update_kpis()
        self.refresh_sales_chart()
        self.draw_category_pie_chart()
        self.load_low_stock_alerts()
        self.load_expiring_items()

    def update_kpis(self):
        products = self.product_manager.get_all_products()
        sales_today = self.sales_manager.get_sales_today()

        total_revenue = sum(s["total"] for s in sales_today)
        low_stock_count = len([p for p in products if p["stock"] <= p.get("min_stock_level", 5)])

        self.kpi_cards[0].findChild(QLabel).setText(f"${total_revenue:,.2f}")
        self.kpi_cards[1].findChild(QLabel).setText(f"${total_revenue:,.2f}")
        self.kpi_cards[2].findChild(QLabel).setText(str(len(products)))
        self.kpi_cards[3].findChild(QLabel).setText(str(low_stock_count))

    def refresh_sales_chart(self):
        grouping = self.grouping_combo.currentText().lower()
        data = self.sales_manager.get_sales_trend(grouping)

        ax = self.bar_canvas.axes
        ax.clear()

        if not data:
            ax.text(0.5, 0.5, "No sales data yet", transform=ax.transAxes,
                    ha='center', va='center', color='#888', fontsize=14)
        else:
            dates = [item["period"] for item in data]
            amounts = [item["total"] for item in data]

            bars = ax.bar(dates, amounts, color='#2196f3', edgecolor='#1976d2', linewidth=1.2)
            ax.set_title(f"Sales Trend - {grouping.title()} View", color='white', fontsize=14, pad=20)
            ax.set_ylabel("Revenue ($)", color='#aaa')
            ax.tick_params(colors='#aaa', labelsize=9)
            ax.grid(axis='y', alpha=0.3, linestyle='--')
            for bar in bars:
                height = bar.get_height()
                ax.text(bar.get_x() + bar.get_width()/2., height + max(amounts)*0.01,
                        f'${height:,.0f}', ha='center', va='bottom', color='white', fontsize=9)

            plt_rot = 45 if grouping == "daily" else 0
            import matplotlib.pyplot as plt
            plt.setp(ax.get_xticklabels(), rotation=plt_rot, ha="right" if plt_rot else "center")

        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        self.bar_canvas.draw()

    def draw_category_pie_chart(self):
        ax = self.pie_canvas.axes
        ax.clear()

        products = self.product_manager.get_all_products()
        from collections import Counter
        categories = [p.get("category", "Uncategorized") for p in products]
        count = Counter(categories)

        if not count:
            ax.text(0.5, 0.5, "No products", transform=ax.transAxes, ha='center', va='center', color='#888')
        else:
            colors = ['#ff6b6b', '#4ecdc4', '#45b7d1', '#f9ca24', '#6c5ce7', '#a29bfe']
            wedges, texts, autotexts = ax.pie(
                count.values(),
                labels=count.keys(),
                autopct='%1.1f%%',
                startangle=90,
                colors=colors[:len(count)],
                textprops={'color': 'white', 'weight': 'bold'},
                wedgeprops={'edgecolor': '#333'}
            )
            for autotext in autotexts:
                autotext.set_color('white')
                autotext.set_fontsize(10)

        ax.set_title("Product Categories", color='white', fontsize=14, pad=20)
        self.pie_canvas.draw()

    def load_low_stock_alerts(self):
        products = self.product_manager.get_all_products()
        low_stock = [p for p in products if p["stock"] <= p.get("min_stock_level", 5)]

        self.low_stock_table.setRowCount(0)
        for p in low_stock:
            row = self.low_stock_table.rowCount()
            self.low_stock_table.insertRow(row)
            self.low_stock_table.setItem(row, 0, QTableWidgetItem(p["name"]))
            self.low_stock_table.setItem(row, 1, QTableWidgetItem(str(p["stock"])))
            self.low_stock_table.setItem(row, 2, QTableWidgetItem(str(p.get("min_stock_level", 5))))
            status = "Out of Stock" if p["stock"] == 0 else "Low Stock"
            badge = BadgeLabel(status, "No Stock" if p["stock"] == 0 else "Low Stock")
            self.low_stock_table.setCellWidget(row, 3, badge)

    def load_expiring_items(self):
        # Placeholder — implement when batch/expiry tracking is added
        self.expiring_table.setRowCount(1)
        self.expiring_table.setItem(0, 0, QTableWidgetItem("No expiry tracking yet"))
        self.expiring_table.setSpan(0, 0, 1, 4)