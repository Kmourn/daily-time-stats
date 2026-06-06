from __future__ import annotations

import json
import shutil
import sqlite3
import tempfile
import zipfile
from datetime import date, datetime
from pathlib import Path
from typing import Optional

from . import __version__
from .constants import (
    APP_DISPLAY_NAME,
    APP_PACKAGE_NAME,
    AUTO_BACKUP_DIR_NAME,
    BACKUP_DIR_NAME,
    DB_FILE_NAME,
    SCHEMA_VERSION,
)
from .database import DataStore
from .utils import format_date, format_datetime


class BackupManager:
    def __init__(self, store: DataStore):
        self.store = store
        self.backup_root = self.store.db_path.parent / BACKUP_DIR_NAME
        self.auto_backup_dir = self.backup_root / AUTO_BACKUP_DIR_NAME
        self.backup_root.mkdir(parents=True, exist_ok=True)
        self.auto_backup_dir.mkdir(parents=True, exist_ok=True)

    def export_backup(self, destination: Path) -> Path:
        destination = Path(destination)
        if destination.suffix.lower() != ".zip":
            destination = destination.with_suffix(".zip")
        destination.parent.mkdir(parents=True, exist_ok=True)
        self._write_backup_zip(destination)
        return destination

    def auto_backup(self, backup_date: date) -> Path:
        path = self.auto_backup_dir / f"{APP_PACKAGE_NAME}-{format_date(backup_date)}.zip"
        backed_at = datetime.now()
        self.store.mark_backup(backup_date, path, backed_at)
        self._write_backup_zip(path, backed_at=backed_at, backup_date=backup_date)
        self._prune_auto_backups(keep=7)
        return path

    def restore_backup(self, source: Path) -> None:
        source = Path(source)
        if not source.exists():
            raise FileNotFoundError(source)
        with tempfile.TemporaryDirectory(prefix=f"{APP_PACKAGE_NAME}-restore-") as temp_dir:
            temp_path = Path(temp_dir)
            with zipfile.ZipFile(source, "r") as zf:
                names = set(zf.namelist())
                if DB_FILE_NAME not in names:
                    raise ValueError("备份文件中未找到数据库")
                zf.extract(DB_FILE_NAME, temp_path)
            extracted_db = temp_path / DB_FILE_NAME
            source_conn = sqlite3.connect(str(extracted_db))
            try:
                source_conn.backup(self.store.conn)
            finally:
                source_conn.close()
            self.store.initialize()

    def _write_backup_zip(
        self,
        destination: Path,
        backed_at: Optional[datetime] = None,
        backup_date: Optional[date] = None,
    ) -> None:
        backed_at = backed_at or datetime.now()
        with tempfile.TemporaryDirectory(prefix=f"{APP_PACKAGE_NAME}-backup-") as temp_dir:
            temp_path = Path(temp_dir)
            db_copy = temp_path / DB_FILE_NAME
            dest_conn = sqlite3.connect(str(db_copy))
            try:
                self.store.conn.backup(dest_conn)
            finally:
                dest_conn.close()

            manifest = {
                "app": APP_PACKAGE_NAME,
                "display_name": APP_DISPLAY_NAME,
                "app_version": __version__,
                "schema_version": SCHEMA_VERSION,
                "created_at": format_datetime(backed_at),
                "backup_date": format_date(backup_date) if backup_date else None,
                "platform": "portable-sqlite",
            }
            manifest_path = temp_path / "manifest.json"
            manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")

            temp_zip = destination.with_suffix(destination.suffix + ".tmp")
            with zipfile.ZipFile(temp_zip, "w", zipfile.ZIP_DEFLATED) as zf:
                zf.write(db_copy, DB_FILE_NAME)
                zf.write(manifest_path, "manifest.json")
            shutil.move(str(temp_zip), str(destination))

    def _prune_auto_backups(self, keep: int) -> None:
        backups = sorted(
            self.auto_backup_dir.glob(f"{APP_PACKAGE_NAME}-*.zip"),
            key=lambda path: path.stat().st_mtime,
            reverse=True,
        )
        for old_path in backups[keep:]:
            old_path.unlink(missing_ok=True)
