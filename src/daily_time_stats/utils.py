from __future__ import annotations

import math
from datetime import date, datetime, time, timedelta

from .constants import DATE_FORMAT, DATETIME_FORMAT, TIME_FORMAT


def parse_date(value: str) -> date:
    return datetime.strptime(value, DATE_FORMAT).date()


def format_date(value: date) -> str:
    return value.strftime(DATE_FORMAT)


def parse_time(value: str) -> time:
    return datetime.strptime(value, TIME_FORMAT).time()


def format_time(value: time) -> str:
    return value.strftime(TIME_FORMAT)


def parse_datetime(value: str) -> datetime:
    return datetime.strptime(value, DATETIME_FORMAT)


def format_datetime(value: datetime) -> str:
    return value.strftime(DATETIME_FORMAT)


def combine_date_time(day: date, clock: time) -> datetime:
    return datetime.combine(day, clock)


def ceil_minutes(seconds: int) -> int:
    if seconds <= 0:
        return 0
    return int(math.ceil(seconds / 60))


def format_duration(seconds: int) -> str:
    minutes = ceil_minutes(seconds)
    hours, mins = divmod(minutes, 60)
    return f"{hours}小时{mins}分钟"


def format_axis_hours(hours: float) -> str:
    minutes = int(round(hours * 60))
    whole_hours, mins = divmod(minutes, 60)
    if whole_hours and mins:
        return f"{whole_hours}h{mins}min"
    if whole_hours:
        return f"{whole_hours}h"
    if mins:
        return f"{mins}min"
    return "0"


def seconds_to_hours(seconds: int) -> float:
    return seconds / 3600 if seconds else 0.0


def week_start(day: date) -> date:
    return day - timedelta(days=day.weekday())


def month_start(day: date) -> date:
    return day.replace(day=1)


def next_month(day: date) -> date:
    if day.month == 12:
        return day.replace(year=day.year + 1, month=1, day=1)
    return day.replace(month=day.month + 1, day=1)


def previous_month(day: date) -> date:
    if day.month == 1:
        return day.replace(year=day.year - 1, month=12, day=1)
    return day.replace(month=day.month - 1, day=1)

