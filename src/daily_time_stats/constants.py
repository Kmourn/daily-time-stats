from pathlib import Path


APP_DISPLAY_NAME = "日记"
APP_PACKAGE_NAME = "daily-time-stats"
ORG_NAME = "daily-time-stats"

TASK_CATEGORIES = ["调研", "学习", "阅读", "代码", "写作", "沟通", "休息"]
WEEKDAY_LABELS = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

DATE_FORMAT = "%Y-%m-%d"
TIME_FORMAT = "%H:%M:%S"
DATETIME_FORMAT = "%Y-%m-%d %H:%M:%S"

DATA_DIR_NAME = APP_PACKAGE_NAME
DB_FILE_NAME = "data.sqlite3"
BACKUP_DIR_NAME = "backups"
AUTO_BACKUP_DIR_NAME = "auto"

SCHEMA_VERSION = 1


def default_data_dir() -> Path:
    return Path.home() / ".local" / "share" / DATA_DIR_NAME


def default_database_path() -> Path:
    return default_data_dir() / DB_FILE_NAME

