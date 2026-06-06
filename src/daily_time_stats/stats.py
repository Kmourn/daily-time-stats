from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Dict, List, Tuple

from .constants import TASK_CATEGORIES, WEEKDAY_LABELS
from .database import DataStore, TimeSegment
from .utils import month_start, next_month, seconds_to_hours, week_start


@dataclass
class SeriesStats:
    total_seconds: int
    category_seconds: Dict[str, int]
    date_seconds: Dict[date, int]
    weekday_seconds: Dict[int, int]


def empty_stats(start: date, end: date) -> SeriesStats:
    category_seconds = {category: 0 for category in TASK_CATEGORIES}
    date_seconds = {}
    cursor = start
    while cursor <= end:
        date_seconds[cursor] = 0
        cursor += timedelta(days=1)
    weekday_seconds = {i: 0 for i in range(7)}
    return SeriesStats(0, category_seconds, date_seconds, weekday_seconds)


def split_segment_by_date(segment: TimeSegment, start: date, end: date) -> List[Tuple[date, int]]:
    range_start = datetime.combine(start, datetime.min.time())
    range_end = datetime.combine(end + timedelta(days=1), datetime.min.time())
    current = max(segment.start_at, range_start)
    final = min(segment.end_at, range_end)
    pieces: List[Tuple[date, int]] = []
    while current < final:
        next_midnight = datetime.combine(current.date() + timedelta(days=1), datetime.min.time())
        piece_end = min(final, next_midnight)
        seconds = max(0, int((piece_end - current).total_seconds()))
        if seconds:
            pieces.append((current.date(), seconds))
        current = piece_end
    return pieces


def collect_range_stats(store: DataStore, start: date, end: date) -> SeriesStats:
    stats = empty_stats(start, end)
    for category, segment in store.segments_between(start, end):
        for piece_date, seconds in split_segment_by_date(segment, start, end):
            stats.total_seconds += seconds
            stats.category_seconds.setdefault(category, 0)
            stats.category_seconds[category] += seconds
            stats.date_seconds.setdefault(piece_date, 0)
            stats.date_seconds[piece_date] += seconds
            stats.weekday_seconds[piece_date.weekday()] += seconds
    return stats


def week_stats(store: DataStore, selected_day: date) -> Tuple[date, date, SeriesStats]:
    start = week_start(selected_day)
    end = start + timedelta(days=6)
    return start, end, collect_range_stats(store, start, end)


def month_stats(store: DataStore, selected_month: date) -> Tuple[date, date, SeriesStats]:
    start = month_start(selected_month)
    end = next_month(start) - timedelta(days=1)
    return start, end, collect_range_stats(store, start, end)


def complete_weeks_in_month(selected_month: date) -> List[Tuple[date, date]]:
    start = month_start(selected_month)
    end = next_month(start) - timedelta(days=1)
    cursor = week_start(start)
    weeks: List[Tuple[date, date]] = []
    while cursor <= end:
        week_end = cursor + timedelta(days=6)
        if cursor >= start and week_end <= end:
            weeks.append((cursor, week_end))
        cursor += timedelta(days=7)
    return weeks


def category_hours(stats: SeriesStats) -> List[float]:
    return [seconds_to_hours(stats.category_seconds.get(category, 0)) for category in TASK_CATEGORIES]


def weekday_hours(stats: SeriesStats) -> List[float]:
    return [seconds_to_hours(stats.weekday_seconds.get(index, 0)) for index in range(7)]


def date_hours(stats: SeriesStats, start: date, days: int) -> List[float]:
    return [seconds_to_hours(stats.date_seconds.get(start + timedelta(days=i), 0)) for i in range(days)]


def half_hour_ticks(max_hours: float, target_count: int = 5) -> Tuple[float, List[float]]:
    if max_hours <= 0:
        return 1.0, [0.0, 0.5, 1.0]
    rounded_max = max(0.5, max_hours)
    step = max(0.5, round((rounded_max / max(1, target_count - 1)) * 2) / 2)
    ymax = step * max(2, int((rounded_max + step - 0.001) / step))
    ticks = []
    value = 0.0
    while value <= ymax + 0.001:
        ticks.append(round(value, 2))
        value += step
    return ymax, ticks


def weekday_labels() -> List[str]:
    return WEEKDAY_LABELS[:]

