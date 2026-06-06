APP_STYLESHEET = """
QMainWindow, QWidget {
    background: #f7f8fb;
    color: #111827;
    font-size: 14px;
}
QTabWidget::pane {
    border: 1px solid #dce3ec;
    background: #f7f8fb;
}
QTabBar::tab {
    background: #ffffff;
    border: 1px solid transparent;
    padding: 10px 22px;
    margin: 4px 4px 0 4px;
    color: #4b5563;
}
QTabBar::tab:selected {
    color: #1d4ed8;
    background: #eef5ff;
    border: 1px solid #b7cdf7;
}
QGroupBox {
    background: #ffffff;
    border: 1px solid #dce3ec;
    border-radius: 8px;
    margin-top: 14px;
    padding: 16px 12px 12px 12px;
    font-weight: 600;
}
QGroupBox::title {
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 4px;
}
QLineEdit, QComboBox, QDateEdit, QDateTimeEdit, QTableWidget, QTreeWidget {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 5px;
}
QPushButton {
    background: #ffffff;
    border: 1px solid #cbd5e1;
    border-radius: 6px;
    padding: 7px 12px;
}
QPushButton:hover {
    background: #f8fafc;
}
QPushButton:checked, QPushButton[primary="true"] {
    color: #ffffff;
    background: #2563eb;
    border: 1px solid #2563eb;
    font-weight: 600;
}
QPushButton[success="true"] {
    color: #ffffff;
    background: #16a34a;
    border: 1px solid #16a34a;
    font-weight: 600;
}
QPushButton[danger="true"] {
    color: #b42318;
}
QPushButton[dark="true"] {
    color: #ffffff;
    background: #111827;
    border: 1px solid #111827;
    font-weight: 600;
}
QLabel[muted="true"] {
    color: #667085;
}
QLabel[total="true"] {
    font-size: 24px;
    font-weight: 700;
}
QHeaderView::section {
    background: #f1f4f8;
    border: none;
    padding: 7px;
    font-weight: 600;
}
"""

