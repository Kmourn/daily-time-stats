from __future__ import annotations

import sqlite3
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from .constants import (
    APP_PACKAGE_NAME,
    SCHEMA_VERSION,
    TASK_CATEGORIES,
    default_database_path,
)
from .utils import format_date, format_datetime, parse_datetime


@dataclass
class TimeSegment:
    id: Optional[int]
    entry_id: Optional[int]
    segment_index: int
    start_at: datetime
    end_at: datetime

    @property
    def seconds(self) -> int:
        return max(0, int((self.end_at - self.start_at).total_seconds()))


@dataclass
class TimeEntry:
    id: Optional[int]
    entry_date: date
    category: str
    content: str
    note: str = ""
    segments: List[TimeSegment] = field(default_factory=list)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    @property
    def seconds(self) -> int:
        return sum(segment.seconds for segment in self.segments)


class DataStore:
    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = Path(db_path) if db_path else default_database_path()
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(self.db_path))
        self.conn.row_factory = sqlite3.Row
        self.conn.execute("PRAGMA foreign_keys = ON")
        self.initialize()

    def close(self) -> None:
        self.conn.close()

    def initialize(self) -> None:
        self.conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS metadata (
                key TEXT PRIMARY KEY,
                value TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_date TEXT NOT NULL,
                category TEXT NOT NULL,
                content TEXT NOT NULL,
                note TEXT NOT NULL DEFAULT '',
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS time_segments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                entry_id INTEGER NOT NULL REFERENCES entries(id) ON DELETE CASCADE,
                segment_index INTEGER NOT NULL,
                start_at TEXT NOT NULL,
                end_at TEXT NOT NULL,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS content_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                category TEXT NOT NULL,
                content TEXT NOT NULL,
                usage_count INTEGER NOT NULL DEFAULT 1,
                active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL,
                UNIQUE(category, content)
            );

            CREATE TABLE IF NOT EXISTS backup_logs (
                backup_date TEXT PRIMARY KEY,
                backup_path TEXT NOT NULL,
                backed_at TEXT NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_entries_date ON entries(entry_date);
            CREATE INDEX IF NOT EXISTS idx_entries_category ON entries(category);
            CREATE INDEX IF NOT EXISTS idx_segments_entry ON time_segments(entry_id);
            CREATE INDEX IF NOT EXISTS idx_segments_range ON time_segments(start_at, end_at);
            CREATE INDEX IF NOT EXISTS idx_memories_category ON content_memories(category, active);
            """
        )
        self.set_metadata("schema_version", str(SCHEMA_VERSION))
        self.set_metadata("app_package", APP_PACKAGE_NAME)
        self.conn.commit()

    def set_metadata(self, key: str, value: str) -> None:
        self.conn.execute(
            """
            INSERT INTO metadata(key, value)
            VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
            """,
            (key, value),
        )

    def get_metadata(self, key: str, default: Optional[str] = None) -> Optional[str]:
        row = self.conn.execute("SELECT value FROM metadata WHERE key = ?", (key,)).fetchone()
        return row["value"] if row else default

    def list_entries(self, entry_date: date) -> List[TimeEntry]:
        rows = self.conn.execute(
            """
            SELECT *
            FROM entries
            WHERE entry_date = ?
            ORDER BY created_at, id
            """,
            (format_date(entry_date),),
        ).fetchall()
        entries = [self._entry_from_row(row) for row in rows]
        if not entries:
            return []
        segments_by_entry = self._segments_for_entries([entry.id for entry in entries if entry.id])
        for entry in entries:
            entry.segments = segments_by_entry.get(entry.id or -1, [])
        return entries

    def get_entry(self, entry_id: int) -> Optional[TimeEntry]:
        row = self.conn.execute("SELECT * FROM entries WHERE id = ?", (entry_id,)).fetchone()
        if not row:
            return None
        entry = self._entry_from_row(row)
        entry.segments = self._segments_for_entries([entry_id]).get(entry_id, [])
        return entry

    def save_entry(self, entry: TimeEntry) -> int:
        now = datetime.now()
        if entry.category not in TASK_CATEGORIES:
            raise ValueError(f"invalid category: {entry.category}")
        if not entry.content.strip():
            raise ValueError("content is required")
        if not entry.segments:
            raise ValueError("at least one time segment is required")

        for index, segment in enumerate(entry.segments, start=1):
            if segment.end_at <= segment.start_at:
                raise ValueError("end time must be later than start time")
            segment.segment_index = index

        with self.conn:
            if entry.id is None:
                cur = self.conn.execute(
                    """
                    INSERT INTO entries(entry_date, category, content, note, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        format_date(entry.entry_date),
                        entry.category,
                        entry.content.strip(),
                        entry.note.strip(),
                        format_datetime(now),
                        format_datetime(now),
                    ),
                )
                entry_id = int(cur.lastrowid)
            else:
                entry_id = int(entry.id)
                self.conn.execute(
                    """
                    UPDATE entries
                    SET entry_date = ?, category = ?, content = ?, note = ?, updated_at = ?
                    WHERE id = ?
                    """,
                    (
                        format_date(entry.entry_date),
                        entry.category,
                        entry.content.strip(),
                        entry.note.strip(),
                        format_datetime(now),
                        entry_id,
                    ),
                )
                self.conn.execute("DELETE FROM time_segments WHERE entry_id = ?", (entry_id,))

            for index, segment in enumerate(entry.segments, start=1):
                self.conn.execute(
                    """
                    INSERT INTO time_segments(entry_id, segment_index, start_at, end_at, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (
                        entry_id,
                        index,
                        format_datetime(segment.start_at),
                        format_datetime(segment.end_at),
                        format_datetime(now),
                        format_datetime(now),
                    ),
                )

            self.remember_content(entry.category, entry.content.strip(), commit=False)
        return entry_id

    def delete_entry(self, entry_id: int) -> None:
        with self.conn:
            self.conn.execute("DELETE FROM entries WHERE id = ?", (entry_id,))

    def remember_content(self, category: str, content: str, commit: bool = True) -> None:
        content = content.strip()
        if not content:
            return
        now = format_datetime(datetime.now())
        self.conn.execute(
            """
            INSERT INTO content_memories(category, content, usage_count, active, created_at, updated_at)
            VALUES (?, ?, 1, 1, ?, ?)
            ON CONFLICT(category, content) DO UPDATE SET
                usage_count = content_memories.usage_count + 1,
                active = 1,
                updated_at = excluded.updated_at
            """,
            (category, content, now, now),
        )
        if commit:
            self.conn.commit()

    def forget_content(self, category: str, content: str) -> None:
        with self.conn:
            self.conn.execute(
                """
                UPDATE content_memories
                SET active = 0, updated_at = ?
                WHERE category = ? AND content = ?
                """,
                (format_datetime(datetime.now()), category, content),
            )

    def list_content_memories(self, category: str) -> List[str]:
        rows = self.conn.execute(
            """
            SELECT content
            FROM content_memories
            WHERE category = ? AND active = 1
            ORDER BY usage_count DESC, updated_at DESC, content
            """,
            (category,),
        ).fetchall()
        return [row["content"] for row in rows]

    def segments_between(self, start_date: date, end_date: date) -> List[Tuple[str, TimeSegment]]:
        start = datetime.combine(start_date, datetime.min.time())
        end = datetime.combine(end_date, datetime.max.time())
        rows = self.conn.execute(
            """
            SELECT e.category, s.*
            FROM time_segments s
            JOIN entries e ON e.id = s.entry_id
            WHERE s.end_at > ? AND s.start_at < ?
            ORDER BY s.start_at, s.id
            """,
            (format_datetime(start), format_datetime(end)),
        ).fetchall()
        return [(row["category"], self._segment_from_row(row)) for row in rows]

    def mark_backup(self, backup_date: date, backup_path: Path, backed_at: Optional[datetime] = None) -> None:
        backed_at = backed_at or datetime.now()
        with self.conn:
            self.conn.execute(
                """
                INSERT INTO backup_logs(backup_date, backup_path, backed_at)
                VALUES (?, ?, ?)
                ON CONFLICT(backup_date) DO UPDATE SET
                    backup_path = excluded.backup_path,
                    backed_at = excluded.backed_at
                """,
                (format_date(backup_date), str(backup_path), format_datetime(backed_at)),
            )

    def backup_status(self, backup_date: date) -> bool:
        row = self.conn.execute(
            "SELECT backed_at FROM backup_logs WHERE backup_date = ?",
            (format_date(backup_date),),
        ).fetchone()
        if not row:
            return False
        backed_at = parse_datetime(row["backed_at"])
        latest = self.latest_change_for_date(backup_date)
        if latest is None:
            return True
        return backed_at >= latest

    def latest_change_for_date(self, entry_date: date) -> Optional[datetime]:
        row = self.conn.execute(
            """
            SELECT MAX(value) AS changed_at
            FROM (
                SELECT updated_at AS value FROM entries WHERE entry_date = ?
                UNION ALL
                SELECT s.updated_at AS value
                FROM time_segments s
                JOIN entries e ON e.id = s.entry_id
                WHERE e.entry_date = ?
            )
            """,
            (format_date(entry_date), format_date(entry_date)),
        ).fetchone()
        if not row or row["changed_at"] is None:
            return None
        return parse_datetime(row["changed_at"])

    def _entry_from_row(self, row: sqlite3.Row) -> TimeEntry:
        return TimeEntry(
            id=int(row["id"]),
            entry_date=date.fromisoformat(row["entry_date"]),
            category=row["category"],
            content=row["content"],
            note=row["note"],
            segments=[],
            created_at=parse_datetime(row["created_at"]),
            updated_at=parse_datetime(row["updated_at"]),
        )

    def _segment_from_row(self, row: sqlite3.Row) -> TimeSegment:
        return TimeSegment(
            id=int(row["id"]),
            entry_id=int(row["entry_id"]),
            segment_index=int(row["segment_index"]),
            start_at=parse_datetime(row["start_at"]),
            end_at=parse_datetime(row["end_at"]),
        )

    def _segments_for_entries(self, entry_ids: Sequence[int]) -> Dict[int, List[TimeSegment]]:
        if not entry_ids:
            return {}
        placeholders = ",".join("?" for _ in entry_ids)
        rows = self.conn.execute(
            f"""
            SELECT *
            FROM time_segments
            WHERE entry_id IN ({placeholders})
            ORDER BY entry_id, segment_index, start_at
            """,
            tuple(entry_ids),
        ).fetchall()
        result: Dict[int, List[TimeSegment]] = {}
        for row in rows:
            segment = self._segment_from_row(row)
            result.setdefault(segment.entry_id or -1, []).append(segment)
        return result
