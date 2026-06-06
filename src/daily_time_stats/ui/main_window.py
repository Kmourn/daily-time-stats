from __future__ import annotations

from datetime import date
from pathlib import Path

from PySide6.QtGui import QAction, QCloseEvent, QIcon
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QMainWindow,
    QMenu,
    QMessageBox,
    QSystemTrayIcon,
    QTabWidget,
)

from ..backup import BackupManager
from ..constants import APP_DISPLAY_NAME, APP_PACKAGE_NAME
from ..database import DataStore
from .stats_pages import MonthStatsPage, WeekStatsPage
from .style import APP_STYLESHEET
from .today_page import TodayPage


class MainWindow(QMainWindow):
    def __init__(self, store: DataStore):
        super().__init__()
        self.store = store
        self.backup_manager = BackupManager(store)
        self.setWindowTitle(APP_DISPLAY_NAME)
        self.setWindowIcon(self._app_icon())
        self.setStyleSheet(APP_STYLESHEET)

        self.tabs = QTabWidget()
        self.today_page = TodayPage(self.store, self.backup_manager)
        self.week_page = WeekStatsPage(self.store)
        self.month_page = MonthStatsPage(self.store)
        self.tabs.addTab(self.today_page, "今日时间统计")
        self.tabs.addTab(self.week_page, "一周时间统计")
        self.tabs.addTab(self.month_page, "一月时间统计")
        self.setCentralWidget(self.tabs)

        self.today_page.data_changed.connect(self._refresh_stats_pages)
        self.today_page.timer_state_changed.connect(self._update_tray_state)

        self._build_menu()
        self._build_tray()

    def closeEvent(self, event: QCloseEvent) -> None:
        if self.today_page.is_timer_running():
            reply = QMessageBox.question(
                self,
                "计时程序正在运行",
                "计时程序正在运行，是否直接退出程序？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                event.ignore()
                return
            self.today_page.finish_timer_and_save()
        event.accept()

    def _build_menu(self) -> None:
        file_menu = self.menuBar().addMenu("文件")
        export_action = QAction("导出备份", self)
        restore_action = QAction("恢复备份", self)
        quit_action = QAction("退出", self)
        export_action.triggered.connect(self._export_backup)
        restore_action.triggered.connect(self._restore_backup)
        quit_action.triggered.connect(self._quit_from_action)
        file_menu.addAction(export_action)
        file_menu.addAction(restore_action)
        file_menu.addSeparator()
        file_menu.addAction(quit_action)

    def _build_tray(self) -> None:
        self.tray = QSystemTrayIcon(self._app_icon(), self)
        self.tray.setToolTip(APP_DISPLAY_NAME)
        menu = QMenu(self)
        show_action = QAction("显示日记", self)
        self.tray_status_action = QAction("当前计时状态：当前未计时", self)
        self.tray_status_action.setEnabled(False)
        self.tray_end_action = QAction("结束当前计时", self)
        quit_action = QAction("退出", self)
        show_action.triggered.connect(self._show_from_tray)
        self.tray_end_action.triggered.connect(self.today_page.finish_timer_and_save)
        quit_action.triggered.connect(self._quit_from_action)
        menu.addAction(show_action)
        menu.addAction(self.tray_status_action)
        menu.addAction(self.tray_end_action)
        menu.addSeparator()
        menu.addAction(quit_action)
        self.tray.setContextMenu(menu)
        self.tray.activated.connect(self._tray_activated)
        self.tray.show()
        self._update_tray_state()

    def _refresh_stats_pages(self) -> None:
        self.week_page.refresh()
        self.month_page.refresh()
        self._update_tray_state()

    def _update_tray_state(self) -> None:
        running = self.today_page.is_timer_running()
        self.tray_status_action.setText("当前计时状态：" + self.today_page.timer_status_text())
        self.tray_end_action.setEnabled(running)

    def _show_from_tray(self) -> None:
        self.showNormal()
        self.raise_()
        self.activateWindow()

    def _tray_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        if reason == QSystemTrayIcon.Trigger:
            self._show_from_tray()

    def _quit_from_action(self) -> None:
        if self.today_page.is_timer_running():
            reply = QMessageBox.question(
                self,
                "计时程序正在运行",
                "计时程序正在运行，是否直接退出程序？",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No,
            )
            if reply != QMessageBox.Yes:
                return
            self.today_page.finish_timer_and_save()
        QApplication.instance().quit()

    def _export_backup(self) -> None:
        default_name = str(Path.home() / f"{APP_PACKAGE_NAME}-backup.zip")
        path, _ = QFileDialog.getSaveFileName(self, "导出备份", default_name, "备份文件 (*.zip)")
        if not path:
            return
        try:
            written = self.backup_manager.export_backup(Path(path))
        except Exception as exc:
            QMessageBox.critical(self, "导出失败", str(exc))
            return
        QMessageBox.information(self, "导出完成", f"备份已导出：\n{written}")

    def _restore_backup(self) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "恢复备份", str(Path.home()), "备份文件 (*.zip)")
        if not path:
            return
        reply = QMessageBox.question(
            self,
            "恢复备份",
            "恢复备份会覆盖当前数据库内容，是否继续？",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        try:
            self.backup_manager.restore_backup(Path(path))
        except Exception as exc:
            QMessageBox.critical(self, "恢复失败", str(exc))
            return
        self.today_page.load_day(date.today())
        self._refresh_stats_pages()
        QMessageBox.information(self, "恢复完成", "备份已恢复。")

    def _app_icon(self) -> QIcon:
        icon_path = Path(__file__).resolve().parents[1] / "assets" / "app-icon.svg"
        return QIcon(str(icon_path))

