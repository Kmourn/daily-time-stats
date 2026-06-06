from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import List, Optional

from PySide6.QtCore import QDate, QDateTime, QTime, QTimer, Qt, Signal
from PySide6.QtWidgets import (
    QAbstractItemView,
    QButtonGroup,
    QComboBox,
    QDateEdit,
    QDateTimeEdit,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QTableWidget,
    QTableWidgetItem,
    QTreeWidget,
    QTreeWidgetItem,
    QVBoxLayout,
    QWidget,
)

from ..backup import BackupManager
from ..constants import TASK_CATEGORIES
from ..database import DataStore, TimeEntry, TimeSegment
from ..utils import format_datetime, format_duration


class TodayPage(QWidget):
    data_changed = Signal()
    timer_state_changed = Signal()

    def __init__(self, store: DataStore, backup_manager: BackupManager):
        super().__init__()
        self.store = store
        self.backup_manager = backup_manager
        self.current_day = date.today()
        self.form_entry_id: Optional[int] = None
        self.form_segments: List[TimeSegment] = []
        self.timer_start: Optional[datetime] = None
        self.timer_entry_id: Optional[int] = None
        self.timer_category = ""
        self.timer_content = ""
        self.timer_note = ""
        self.elapsed_timer = QTimer(self)
        self.elapsed_timer.setInterval(1000)
        self.elapsed_timer.timeout.connect(self._refresh_timer_display)

        self._build_ui()
        self.load_day(date.today())

    def is_timer_running(self) -> bool:
        return self.timer_start is not None

    def timer_status_text(self) -> str:
        if not self.timer_start:
            return "当前未计时"
        return f"计时中：{self.timer_category} / {self.timer_content}"

    def load_day(self, day: date) -> None:
        self.current_day = day
        self.date_edit.blockSignals(True)
        self.date_edit.setDate(QDate(day.year, day.month, day.day))
        self.date_edit.blockSignals(False)
        self._set_default_segment_times()
        self._clear_form(keep_date=True)
        self._refresh_entries()
        self._refresh_backup_status()

    def finish_timer_and_save(self) -> bool:
        if not self.timer_start:
            return True
        end_at = datetime.now().replace(microsecond=0)
        if end_at <= self.timer_start:
            end_at = self.timer_start + timedelta(seconds=1)
        segment = TimeSegment(None, None, 1, self.timer_start, end_at)
        target_entry = self._timer_target_entry()
        target_entry.segments.append(segment)
        self.store.save_entry(target_entry)

        self.timer_start = None
        self.timer_entry_id = None
        self.elapsed_timer.stop()
        self._refresh_timer_display()
        self._set_timer_controls(False)
        self._refresh_entries()
        self._refresh_backup_status()
        self.data_changed.emit()
        self.timer_state_changed.emit()
        return True

    def _build_ui(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(18, 18, 18, 18)
        root.setSpacing(12)

        root.addWidget(self._build_date_bar())

        top = QHBoxLayout()
        top.setSpacing(14)
        top.addWidget(self._build_form_group(), 2)
        top.addWidget(self._build_timer_group(), 1)
        root.addLayout(top)

        root.addWidget(self._build_entries_group(), 1)
        root.addLayout(self._build_bottom_bar())

    def _build_date_bar(self) -> QWidget:
        box = QGroupBox("")
        layout = QHBoxLayout(box)
        layout.setContentsMargins(14, 12, 14, 12)
        layout.addWidget(QLabel("日期"))
        prev_btn = QPushButton("<")
        next_btn = QPushButton(">")
        today_btn = QPushButton("今天")
        today_btn.setProperty("success", True)
        self.date_edit = QDateEdit()
        self.date_edit.setCalendarPopup(True)
        self.date_edit.setDisplayFormat("yyyy-MM-dd")
        self.date_edit.dateChanged.connect(self._on_date_changed)
        prev_btn.clicked.connect(lambda: self.load_day(self.current_day - timedelta(days=1)))
        next_btn.clicked.connect(lambda: self.load_day(self.current_day + timedelta(days=1)))
        today_btn.clicked.connect(lambda: self.load_day(date.today()))
        layout.addWidget(prev_btn)
        layout.addWidget(self.date_edit)
        layout.addWidget(next_btn)
        layout.addWidget(today_btn)
        layout.addStretch(1)
        layout.addWidget(QLabel("当日总计"))
        self.day_total_label = QLabel("0小时0分钟")
        self.day_total_label.setProperty("total", True)
        layout.addWidget(self.day_total_label)
        return box

    def _build_form_group(self) -> QWidget:
        group = QGroupBox("新增 / 编辑条目")
        layout = QGridLayout(group)
        layout.setHorizontalSpacing(10)
        layout.setVerticalSpacing(8)

        layout.addWidget(QLabel("事项"), 0, 0)
        category_layout = QHBoxLayout()
        self.category_group = QButtonGroup(self)
        self.category_group.setExclusive(True)
        for index, category in enumerate(TASK_CATEGORIES):
            btn = QPushButton(category)
            btn.setCheckable(True)
            self.category_group.addButton(btn, index)
            category_layout.addWidget(btn)
            if index == 0:
                btn.setChecked(True)
        self.category_group.idClicked.connect(self._on_category_changed)
        layout.addLayout(category_layout, 0, 1, 1, 4)

        layout.addWidget(QLabel("内容"), 1, 0)
        self.content_combo = QComboBox()
        self.content_combo.setEditable(True)
        layout.addWidget(self.content_combo, 1, 1, 1, 2)

        layout.addWidget(QLabel("备注"), 1, 3)
        self.note_edit = QLineEdit()
        layout.addWidget(self.note_edit, 1, 4)

        self.start_edit = QDateTimeEdit()
        self.start_edit.setCalendarPopup(True)
        self.start_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        self.end_edit = QDateTimeEdit()
        self.end_edit.setCalendarPopup(True)
        self.end_edit.setDisplayFormat("yyyy-MM-dd HH:mm:ss")
        add_segment_btn = QPushButton("+ 新增时间段")
        add_segment_btn.setProperty("primary", True)
        add_segment_btn.clicked.connect(self._add_form_segment)
        layout.addWidget(QLabel("开始"), 2, 0)
        layout.addWidget(self.start_edit, 2, 1)
        layout.addWidget(QLabel("结束"), 2, 2)
        layout.addWidget(self.end_edit, 2, 3)
        layout.addWidget(add_segment_btn, 2, 4)

        self.segment_table = QTableWidget(0, 4)
        self.segment_table.setHorizontalHeaderLabels(["段", "开始", "结束", "时长"])
        self.segment_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.segment_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.segment_table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        layout.addWidget(self.segment_table, 3, 0, 1, 5)

        remove_segment_btn = QPushButton("删除所选时间段")
        remove_segment_btn.clicked.connect(self._remove_selected_form_segment)
        save_btn = QPushButton("保存条目")
        save_btn.setProperty("primary", True)
        save_btn.clicked.connect(self._save_form_entry)
        clear_btn = QPushButton("清空")
        clear_btn.clicked.connect(lambda: self._clear_form(keep_date=True))
        action_layout = QHBoxLayout()
        action_layout.addStretch(1)
        action_layout.addWidget(remove_segment_btn)
        action_layout.addWidget(save_btn)
        action_layout.addWidget(clear_btn)
        layout.addLayout(action_layout, 4, 0, 1, 5)

        self._refresh_content_memories()
        self._set_default_segment_times()
        return group

    def _build_timer_group(self) -> QWidget:
        group = QGroupBox("计时器")
        layout = QVBoxLayout(group)
        layout.addWidget(QLabel("当前选择"))
        self.timer_target_label = QLabel("请先选择事项和内容")
        self.timer_target_label.setWordWrap(True)
        layout.addWidget(self.timer_target_label)
        self.timer_label = QLabel("00:00:00")
        self.timer_label.setAlignment(Qt.AlignCenter)
        self.timer_label.setStyleSheet("font-size: 36px; font-weight: 700;")
        layout.addWidget(self.timer_label)
        buttons = QHBoxLayout()
        self.start_timer_btn = QPushButton("开始")
        self.start_timer_btn.setProperty("success", True)
        self.end_timer_btn = QPushButton("结束")
        self.end_timer_btn.setEnabled(False)
        self.start_timer_btn.clicked.connect(self._start_timer)
        self.end_timer_btn.clicked.connect(self.finish_timer_and_save)
        buttons.addWidget(self.start_timer_btn)
        buttons.addWidget(self.end_timer_btn)
        layout.addLayout(buttons)
        self.timer_status_label = QLabel("状态：当前未计时")
        self.timer_status_label.setProperty("muted", True)
        layout.addWidget(self.timer_status_label)
        layout.addStretch(1)
        self.content_combo.currentTextChanged.connect(self._refresh_timer_target)
        return group

    def _build_entries_group(self) -> QWidget:
        group = QGroupBox("当日条目")
        layout = QVBoxLayout(group)
        self.entries_tree = QTreeWidget()
        self.entries_tree.setColumnCount(5)
        self.entries_tree.setHeaderLabels(["事项", "内容", "时间段", "时长", "备注"])
        self.entries_tree.header().setSectionResizeMode(QHeaderView.Stretch)
        self.entries_tree.setSelectionMode(QAbstractItemView.SingleSelection)
        layout.addWidget(self.entries_tree)
        buttons = QHBoxLayout()
        edit_btn = QPushButton("编辑选中条目")
        delete_btn = QPushButton("删除选中")
        delete_btn.setProperty("danger", True)
        expand_btn = QPushButton("展开全部")
        edit_btn.clicked.connect(self._edit_selected_entry)
        delete_btn.clicked.connect(self._delete_selected)
        expand_btn.clicked.connect(self.entries_tree.expandAll)
        buttons.addStretch(1)
        buttons.addWidget(expand_btn)
        buttons.addWidget(edit_btn)
        buttons.addWidget(delete_btn)
        layout.addLayout(buttons)
        return group

    def _build_bottom_bar(self) -> QHBoxLayout:
        layout = QHBoxLayout()
        self.backup_hint = QLabel("自动备份保留最近 7 份")
        self.backup_hint.setProperty("muted", True)
        self.complete_btn = QPushButton("今日事项完毕")
        self.complete_btn.setProperty("dark", True)
        self.complete_btn.clicked.connect(self._complete_today)
        self.backup_status_label = QLabel("本日数据未备份")
        layout.addWidget(self.backup_hint)
        layout.addStretch(1)
        layout.addWidget(self.complete_btn)
        layout.addWidget(self.backup_status_label)
        layout.addStretch(1)
        return layout

    def _selected_category(self) -> str:
        btn = self.category_group.checkedButton()
        return btn.text() if btn else TASK_CATEGORIES[0]

    def _on_date_changed(self, qdate: QDate) -> None:
        self.load_day(date(qdate.year(), qdate.month(), qdate.day()))

    def _on_category_changed(self, _button_id: int) -> None:
        self._refresh_content_memories()
        self._refresh_timer_target()

    def _refresh_content_memories(self) -> None:
        category = self._selected_category()
        current_text = self.content_combo.currentText().strip()
        self.content_combo.blockSignals(True)
        self.content_combo.clear()
        self.content_combo.addItems(self.store.list_content_memories(category))
        self.content_combo.setEditText(current_text)
        self.content_combo.blockSignals(False)

    def _refresh_timer_target(self) -> None:
        content = self.content_combo.currentText().strip()
        self.timer_target_label.setText(
            f"{self._selected_category()} / {content}" if content else "请先选择事项和内容"
        )

    def _set_default_segment_times(self) -> None:
        start = datetime.combine(self.current_day, datetime.now().time()).replace(microsecond=0)
        end = start + timedelta(minutes=30)
        self.start_edit.setDateTime(self._to_qdatetime(start))
        self.end_edit.setDateTime(self._to_qdatetime(end))

    def _add_form_segment(self) -> None:
        start_at = self._from_qdatetime(self.start_edit.dateTime())
        end_at = self._from_qdatetime(self.end_edit.dateTime())
        if end_at <= start_at:
            QMessageBox.warning(self, "时间错误", "结束时间必须晚于开始时间。")
            return
        self.form_segments.append(TimeSegment(None, self.form_entry_id, len(self.form_segments) + 1, start_at, end_at))
        self._refresh_segment_table()
        self.start_edit.setDateTime(self._to_qdatetime(end_at))
        self.end_edit.setDateTime(self._to_qdatetime(end_at + timedelta(minutes=30)))

    def _remove_selected_form_segment(self) -> None:
        row = self.segment_table.currentRow()
        if row < 0 or row >= len(self.form_segments):
            return
        del self.form_segments[row]
        for index, segment in enumerate(self.form_segments, start=1):
            segment.segment_index = index
        self._refresh_segment_table()

    def _refresh_segment_table(self) -> None:
        self.segment_table.setRowCount(len(self.form_segments))
        for row, segment in enumerate(self.form_segments):
            values = [
                f"第{row + 1}段",
                format_datetime(segment.start_at),
                format_datetime(segment.end_at),
                format_duration(segment.seconds),
            ]
            for col, value in enumerate(values):
                self.segment_table.setItem(row, col, QTableWidgetItem(value))

    def _save_form_entry(self) -> None:
        content = self.content_combo.currentText().strip()
        if not content:
            QMessageBox.warning(self, "内容缺失", "请填写内容。")
            return
        if not self.form_segments:
            QMessageBox.warning(self, "时间段缺失", "请至少新增一段时间。")
            return
        entry = TimeEntry(
            id=self.form_entry_id,
            entry_date=self.current_day,
            category=self._selected_category(),
            content=content,
            note=self.note_edit.text(),
            segments=list(self.form_segments),
        )
        try:
            self.store.save_entry(entry)
        except ValueError as exc:
            QMessageBox.warning(self, "保存失败", str(exc))
            return
        self._clear_form(keep_date=True)
        self._refresh_entries()
        self._refresh_backup_status()
        self.data_changed.emit()

    def _clear_form(self, keep_date: bool = False) -> None:
        self.form_entry_id = None
        self.form_segments = []
        self.content_combo.setEditText("")
        self.note_edit.clear()
        self._refresh_segment_table()
        if not keep_date:
            self.load_day(date.today())
        else:
            self._set_default_segment_times()
        self._refresh_timer_target()

    def _refresh_entries(self) -> None:
        entries = self.store.list_entries(self.current_day)
        total_seconds = sum(entry.seconds for entry in entries)
        self.day_total_label.setText(format_duration(total_seconds))
        self.entries_tree.clear()
        for entry in entries:
            item = QTreeWidgetItem(
                [
                    entry.category,
                    entry.content,
                    f"共{len(entry.segments)}段",
                    format_duration(entry.seconds),
                    entry.note or "-",
                ]
            )
            item.setData(0, Qt.UserRole, ("entry", entry.id))
            for segment in entry.segments:
                child = QTreeWidgetItem(
                    [
                        "",
                        f"第{segment.segment_index}段",
                        f"{format_datetime(segment.start_at)} - {format_datetime(segment.end_at)}",
                        format_duration(segment.seconds),
                        "",
                    ]
                )
                child.setData(0, Qt.UserRole, ("segment", entry.id, segment.id))
                item.addChild(child)
            self.entries_tree.addTopLevelItem(item)
        self.entries_tree.expandAll()

    def _edit_selected_entry(self) -> None:
        entry_id = self._selected_entry_id()
        if entry_id is None:
            return
        entry = self.store.get_entry(entry_id)
        if not entry:
            return
        self.form_entry_id = entry.id
        self._set_category(entry.category)
        self._refresh_content_memories()
        self.content_combo.setEditText(entry.content)
        self.note_edit.setText(entry.note)
        self.form_segments = [
            TimeSegment(segment.id, entry.id, segment.segment_index, segment.start_at, segment.end_at)
            for segment in entry.segments
        ]
        self._refresh_segment_table()
        self._refresh_timer_target()

    def _delete_selected(self) -> None:
        selected = self.entries_tree.currentItem()
        if not selected:
            return
        data = selected.data(0, Qt.UserRole)
        if not data:
            return
        if data[0] == "entry":
            entry_id = int(data[1])
            if QMessageBox.question(self, "删除条目", "确定删除选中条目吗？") != QMessageBox.Yes:
                return
            self.store.delete_entry(entry_id)
        elif data[0] == "segment":
            entry_id = int(data[1])
            segment_id = int(data[2])
            entry = self.store.get_entry(entry_id)
            if not entry:
                return
            if QMessageBox.question(self, "删除时间段", "确定删除选中时间段吗？") != QMessageBox.Yes:
                return
            entry.segments = [segment for segment in entry.segments if segment.id != segment_id]
            if entry.segments:
                self.store.save_entry(entry)
            else:
                self.store.delete_entry(entry_id)
        self._refresh_entries()
        self._refresh_backup_status()
        self.data_changed.emit()

    def _selected_entry_id(self) -> Optional[int]:
        selected = self.entries_tree.currentItem()
        if not selected:
            return None
        data = selected.data(0, Qt.UserRole)
        if not data:
            return None
        if data[0] == "entry":
            return int(data[1])
        if data[0] == "segment":
            return int(data[1])
        return None

    def _set_category(self, category: str) -> None:
        for button in self.category_group.buttons():
            button.setChecked(button.text() == category)

    def _start_timer(self) -> None:
        content = self.content_combo.currentText().strip()
        if not content:
            QMessageBox.warning(self, "内容缺失", "开始计时前请先填写内容。")
            return
        self.timer_start = datetime.now().replace(microsecond=0)
        self.timer_entry_id = self.form_entry_id
        self.timer_category = self._selected_category()
        self.timer_content = content
        self.timer_note = self.note_edit.text()
        self.elapsed_timer.start()
        self._set_timer_controls(True)
        self._refresh_timer_display()
        self.timer_state_changed.emit()

    def _timer_target_entry(self) -> TimeEntry:
        if self.timer_entry_id:
            entry = self.store.get_entry(self.timer_entry_id)
            if entry:
                return entry
        for entry in self.store.list_entries(self.current_day):
            if (
                entry.category == self.timer_category
                and entry.content == self.timer_content
                and entry.note == self.timer_note
            ):
                return entry
        return TimeEntry(
            id=None,
            entry_date=self.current_day,
            category=self.timer_category,
            content=self.timer_content,
            note=self.timer_note,
            segments=[],
        )

    def _set_timer_controls(self, running: bool) -> None:
        self.start_timer_btn.setEnabled(not running)
        self.end_timer_btn.setEnabled(running)
        self.timer_status_label.setText("状态：" + self.timer_status_text())

    def _refresh_timer_display(self) -> None:
        if not self.timer_start:
            self.timer_label.setText("00:00:00")
            self.timer_status_label.setText("状态：当前未计时")
            return
        elapsed = max(0, int((datetime.now() - self.timer_start).total_seconds()))
        hours, rem = divmod(elapsed, 3600)
        minutes, seconds = divmod(rem, 60)
        self.timer_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")
        self.timer_status_label.setText("状态：" + self.timer_status_text())

    def _complete_today(self) -> None:
        try:
            self.backup_manager.auto_backup(self.current_day)
        except Exception as exc:
            QMessageBox.critical(self, "备份失败", str(exc))
            return
        self._refresh_backup_status()
        QMessageBox.information(self, "备份完成", "本日数据已备份。")

    def _refresh_backup_status(self) -> None:
        backed = self.store.backup_status(self.current_day)
        self.backup_status_label.setText("本日数据已备份" if backed else "本日数据未备份")
        self.backup_status_label.setStyleSheet("color: #166534;" if backed else "color: #b45309;")

    @staticmethod
    def _to_qdatetime(value: datetime) -> QDateTime:
        return QDateTime(
            QDate(value.year, value.month, value.day),
            QTime(value.hour, value.minute, value.second),
        )

    @staticmethod
    def _from_qdatetime(value: QDateTime) -> datetime:
        qdate = value.date()
        qtime = value.time()
        return datetime(
            qdate.year(),
            qdate.month(),
            qdate.day(),
            qtime.hour(),
            qtime.minute(),
            qtime.second(),
        )
