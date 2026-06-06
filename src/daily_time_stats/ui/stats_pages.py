from __future__ import annotations

from datetime import date, timedelta
from typing import List

from PySide6.QtCore import QDate, Qt
from PySide6.QtWidgets import (
    QButtonGroup,
    QDateEdit,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..constants import TASK_CATEGORIES, WEEKDAY_LABELS
from ..database import DataStore
from ..stats import (
    category_hours,
    collect_range_stats,
    complete_weeks_in_month,
    month_stats,
    week_stats,
    weekday_hours,
)
from ..utils import (
    format_date,
    format_duration,
    month_start,
    next_month,
    previous_month,
)
from .charts import make_bar_chart, make_line_chart


PALETTE = ["#2563eb", "#16a34a", "#f59e0b", "#7c3aed", "#0891b2"]
PREVIOUS_COLOR = "#94a3b8"


class WeekStatsPage(QWidget):
    def __init__(self, store: DataStore):
        super().__init__()
        self.store = store
        self.selected_day = date.today()
        self.compare = False
        self._build_ui()
        self.refresh()

    def refresh(self) -> None:
        start, end, current = week_stats(self.store, self.selected_day)
        self.date_picker.blockSignals(True)
        self.date_picker.setDate(QDate(self.selected_day.year, self.selected_day.month, self.selected_day.day))
        self.date_picker.blockSignals(False)
        self.range_label.setText(f"{format_date(start)} 至 {format_date(end)}")
        if self.compare:
            prev_start, prev_end = start - timedelta(days=7), end - timedelta(days=7)
            previous = collect_range_stats(self.store, prev_start, prev_end)
            self.prev_total_label.setText(f"上周总时长  {format_duration(previous.total_seconds)}")
            self.prev_total_label.show()
            bar_series = [
                ("上周", category_hours(previous), PREVIOUS_COLOR),
                ("本周", category_hours(current), PALETTE[0]),
            ]
            line_series = [
                ("上周", weekday_hours(previous), PREVIOUS_COLOR),
                ("本周", weekday_hours(current), PALETTE[0]),
            ]
            self.compare_btn.setText("关闭对比")
        else:
            bar_series = [("本周", category_hours(current), PALETTE[0])]
            line_series = [("本周", weekday_hours(current), PALETTE[0])]
            self.prev_total_label.hide()
            self.compare_btn.setText("与上周对比")
        self.total_label.setText(f"本周总时长  {format_duration(current.total_seconds)}")
        self._replace_charts(
            make_bar_chart("事项用时", TASK_CATEGORIES, bar_series),
            make_line_chart("每日用时", WEEKDAY_LABELS, line_series),
        )

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)
        root.addWidget(self._build_range_bar())
        root.addWidget(self._build_total_card())
        charts = QHBoxLayout()
        charts.setSpacing(14)
        self.left_chart_box = QGroupBox("")
        self.right_chart_box = QGroupBox("")
        self.left_chart_layout = QVBoxLayout(self.left_chart_box)
        self.right_chart_layout = QVBoxLayout(self.right_chart_box)
        charts.addWidget(self.left_chart_box, 1)
        charts.addWidget(self.right_chart_box, 1)
        root.addLayout(charts, 1)
        bottom = QHBoxLayout()
        bottom.addStretch(1)
        self.compare_btn = QPushButton("与上周对比")
        self.compare_btn.setProperty("dark", True)
        self.compare_btn.clicked.connect(self._toggle_compare)
        bottom.addWidget(self.compare_btn)
        bottom.addStretch(1)
        root.addLayout(bottom)

    def _build_range_bar(self) -> QWidget:
        group = QGroupBox("")
        layout = QHBoxLayout(group)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.addWidget(QLabel("周范围"))
        prev_btn = QPushButton("<")
        next_btn = QPushButton(">")
        current_btn = QPushButton("本期")
        current_btn.setProperty("success", True)
        self.range_label = QLabel("")
        self.range_label.setMinimumWidth(230)
        prev_btn.clicked.connect(lambda: self._move_week(-1))
        next_btn.clicked.connect(lambda: self._move_week(1))
        current_btn.clicked.connect(lambda: self._set_day(date.today()))
        layout.addWidget(prev_btn)
        layout.addWidget(self.range_label)
        layout.addWidget(next_btn)
        layout.addWidget(current_btn)
        layout.addStretch(1)
        self.date_picker = QDateEdit()
        self.date_picker.setCalendarPopup(True)
        self.date_picker.setDisplayFormat("yyyy-MM-dd")
        self.date_picker.dateChanged.connect(self._picked_date)
        layout.addWidget(QLabel("选择日期"))
        layout.addWidget(self.date_picker)
        return group

    def _build_total_card(self) -> QWidget:
        group = QGroupBox("")
        layout = QVBoxLayout(group)
        self.prev_total_label = QLabel("")
        self.prev_total_label.setAlignment(Qt.AlignCenter)
        self.prev_total_label.setProperty("muted", True)
        self.total_label = QLabel("")
        self.total_label.setAlignment(Qt.AlignCenter)
        self.total_label.setProperty("total", True)
        layout.addWidget(self.prev_total_label)
        layout.addWidget(self.total_label)
        return group

    def _replace_charts(self, left: QWidget, right: QWidget) -> None:
        _clear_layout(self.left_chart_layout)
        _clear_layout(self.right_chart_layout)
        self.left_chart_layout.addWidget(left)
        self.right_chart_layout.addWidget(right)

    def _toggle_compare(self) -> None:
        self.compare = not self.compare
        self.refresh()

    def _move_week(self, direction: int) -> None:
        self._set_day(self.selected_day + timedelta(days=direction * 7))

    def _set_day(self, day: date) -> None:
        self.selected_day = day
        self.date_picker.blockSignals(True)
        self.date_picker.setDate(QDate(day.year, day.month, day.day))
        self.date_picker.blockSignals(False)
        self.refresh()

    def _picked_date(self, qdate: QDate) -> None:
        self._set_day(date(qdate.year(), qdate.month(), qdate.day()))


class MonthStatsPage(QWidget):
    def __init__(self, store: DataStore):
        super().__init__()
        self.store = store
        self.selected_month = month_start(date.today())
        self.week_mode = False
        self._build_ui()
        self.refresh()

    def refresh(self) -> None:
        start, _end, stats = month_stats(self.store, self.selected_month)
        self.month_label.setText(f"{start.year:04d}-{start.month:02d}")
        self.total_label.setText(f"本月总时长  {format_duration(stats.total_seconds)}")
        self.day_mode_btn.setChecked(not self.week_mode)
        self.week_mode_btn.setChecked(self.week_mode)
        if self.week_mode:
            self._refresh_week_mode()
        else:
            self.hint_label.setText("当前模式：按星期聚合显示本月各星期用时")
            self._replace_charts(
                make_bar_chart("事项用时", TASK_CATEGORIES, [("本月", category_hours(stats), PALETTE[0])]),
                make_line_chart("每日用时", WEEKDAY_LABELS, [("本月", weekday_hours(stats), PALETTE[0])]),
            )

    def _refresh_week_mode(self) -> None:
        weeks = complete_weeks_in_month(self.selected_month)
        bar_series = []
        line_series = []
        for index, (week_start_day, week_end_day) in enumerate(weeks):
            stats = collect_range_stats(self.store, week_start_day, week_end_day)
            name = _week_name(index)
            color = PALETTE[index % len(PALETTE)]
            bar_series.append((name, category_hours(stats), color))
            line_series.append((name, weekday_hours(stats), color))
        if not bar_series:
            bar_series = [("无完整周", [0 for _ in TASK_CATEGORIES], PALETTE[0])]
            line_series = [("无完整周", [0 for _ in WEEKDAY_LABELS], PALETTE[0])]
        self.hint_label.setText("纳入统计周：周一、周日均在本月内的完整周")
        self._replace_charts(
            make_bar_chart("事项用时", TASK_CATEGORIES, bar_series),
            make_line_chart("每日用时", WEEKDAY_LABELS, line_series),
        )

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)
        root.addWidget(self._build_month_bar())
        root.addWidget(self._build_total_card())
        charts = QHBoxLayout()
        charts.setSpacing(14)
        self.left_chart_box = QGroupBox("")
        self.right_chart_box = QGroupBox("")
        self.left_chart_layout = QVBoxLayout(self.left_chart_box)
        self.right_chart_layout = QVBoxLayout(self.right_chart_box)
        charts.addWidget(self.left_chart_box, 1)
        charts.addWidget(self.right_chart_box, 1)
        root.addLayout(charts, 1)
        self.hint_label = QLabel("")
        self.hint_label.setProperty("muted", True)
        root.addWidget(self.hint_label)

    def _build_month_bar(self) -> QWidget:
        group = QGroupBox("")
        layout = QHBoxLayout(group)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.addWidget(QLabel("月份"))
        prev_btn = QPushButton("<")
        next_btn = QPushButton(">")
        current_btn = QPushButton("本期")
        current_btn.setProperty("success", True)
        self.month_label = QLabel("")
        self.month_label.setMinimumWidth(230)
        prev_btn.clicked.connect(lambda: self._move_month(-1))
        next_btn.clicked.connect(lambda: self._move_month(1))
        current_btn.clicked.connect(lambda: self._set_month(month_start(date.today())))
        layout.addWidget(prev_btn)
        layout.addWidget(self.month_label)
        layout.addWidget(next_btn)
        layout.addWidget(current_btn)
        layout.addStretch(1)
        self.day_mode_btn = QPushButton("按日统计")
        self.week_mode_btn = QPushButton("按周统计")
        self.day_mode_btn.setCheckable(True)
        self.week_mode_btn.setCheckable(True)
        self.mode_group = QButtonGroup(self)
        self.mode_group.setExclusive(True)
        self.mode_group.addButton(self.day_mode_btn, 0)
        self.mode_group.addButton(self.week_mode_btn, 1)
        self.mode_group.idClicked.connect(self._mode_clicked)
        layout.addWidget(self.day_mode_btn)
        layout.addWidget(self.week_mode_btn)
        return group

    def _build_total_card(self) -> QWidget:
        group = QGroupBox("")
        layout = QVBoxLayout(group)
        self.total_label = QLabel("")
        self.total_label.setAlignment(Qt.AlignCenter)
        self.total_label.setProperty("total", True)
        layout.addWidget(self.total_label)
        return group

    def _replace_charts(self, left: QWidget, right: QWidget) -> None:
        _clear_layout(self.left_chart_layout)
        _clear_layout(self.right_chart_layout)
        self.left_chart_layout.addWidget(left)
        self.right_chart_layout.addWidget(right)

    def _move_month(self, direction: int) -> None:
        next_value = next_month(self.selected_month) if direction > 0 else previous_month(self.selected_month)
        self._set_month(next_value)

    def _set_month(self, month: date) -> None:
        self.selected_month = month_start(month)
        self.refresh()

    def _mode_clicked(self, mode_id: int) -> None:
        self.week_mode = mode_id == 1
        self.refresh()


def _clear_layout(layout: QVBoxLayout) -> None:
    while layout.count():
        item = layout.takeAt(0)
        widget = item.widget()
        if widget:
            widget.setParent(None)
            widget.deleteLater()


def _week_name(index: int) -> str:
    names = ["第一周", "第二周", "第三周", "第四周", "第五周"]
    if index < len(names):
        return names[index]
    return f"第{index + 1}周"
