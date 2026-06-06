from __future__ import annotations

from typing import List, Sequence, Tuple

from PySide6.QtCharts import (
    QBarCategoryAxis,
    QBarSeries,
    QBarSet,
    QCategoryAxis,
    QChart,
    QChartView,
    QLineSeries,
)
from PySide6.QtCore import QPointF, Qt
from PySide6.QtGui import QColor, QPainter, QPen

from ..stats import half_hour_ticks
from ..utils import format_axis_hours


ChartSeries = Tuple[str, Sequence[float], str]


def chart_view(chart: QChart) -> QChartView:
    view = QChartView(chart)
    view.setRenderHint(QPainter.Antialiasing)
    view.setMinimumHeight(280)
    return view


def make_bar_chart(title: str, labels: Sequence[str], series_data: Sequence[ChartSeries]) -> QChartView:
    chart = _base_chart(title)
    series = QBarSeries()
    max_value = 0.0
    for name, values, color in series_data:
        bar_set = QBarSet(name)
        bar_set.setColor(QColor(color))
        for value in values:
            bar_set.append(float(value))
            max_value = max(max_value, float(value))
        series.append(bar_set)
    chart.addSeries(series)

    axis_x = QBarCategoryAxis()
    axis_x.append(list(labels))
    axis_x.setLabelsAngle(0)

    axis_y = _hours_axis(max_value)
    chart.addAxis(axis_x, Qt.AlignBottom)
    chart.addAxis(axis_y, Qt.AlignLeft)
    series.attachAxis(axis_x)
    series.attachAxis(axis_y)
    chart.legend().setVisible(len(series_data) > 1)
    chart.legend().setAlignment(Qt.AlignTop)
    return chart_view(chart)


def make_line_chart(title: str, labels: Sequence[str], series_data: Sequence[ChartSeries]) -> QChartView:
    chart = _base_chart(title)
    max_value = 0.0
    line_series = []
    for name, values, color in series_data:
        series = QLineSeries()
        series.setName(name)
        pen = QPen(QColor(color))
        pen.setWidth(3)
        series.setPen(pen)
        for index, value in enumerate(values):
            max_value = max(max_value, float(value))
            series.append(QPointF(index, float(value)))
        chart.addSeries(series)
        line_series.append(series)

    axis_x = QCategoryAxis()
    axis_x.setRange(0, max(0, len(labels) - 1))
    _set_axis_labels_on_value(axis_x)
    for index, label in enumerate(labels):
        axis_x.append(label, float(index))

    axis_y = _hours_axis(max_value)
    chart.addAxis(axis_x, Qt.AlignBottom)
    chart.addAxis(axis_y, Qt.AlignLeft)
    for series in line_series:
        series.attachAxis(axis_x)
        series.attachAxis(axis_y)
    chart.legend().setVisible(len(series_data) > 1)
    chart.legend().setAlignment(Qt.AlignTop)
    return chart_view(chart)


def _base_chart(title: str) -> QChart:
    chart = QChart()
    chart.setTitle(title)
    chart.setAnimationOptions(QChart.SeriesAnimations)
    chart.setBackgroundVisible(False)
    chart.setMargins(chart.margins())
    return chart


def _hours_axis(max_value: float) -> QCategoryAxis:
    ymax, ticks = half_hour_ticks(max_value)
    axis = QCategoryAxis()
    axis.setRange(0, ymax)
    axis.setGridLineVisible(True)
    _set_axis_labels_on_value(axis)
    for tick in ticks:
        axis.append(format_axis_hours(tick), tick)
    return axis


def _set_axis_labels_on_value(axis: QCategoryAxis) -> None:
    try:
        axis.setLabelsPosition(QCategoryAxis.AxisLabelsPositionOnValue)
    except AttributeError:
        try:
            axis.setLabelsPosition(QCategoryAxis.AxisLabelsPosition.AxisLabelsPositionOnValue)
        except AttributeError:
            pass

