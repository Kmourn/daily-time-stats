from __future__ import annotations

import os
import sys

from PySide6.QtCore import QCoreApplication
from PySide6.QtWidgets import QApplication

from .constants import APP_DISPLAY_NAME, APP_PACKAGE_NAME, ORG_NAME
from .database import DataStore
from .ui.main_window import MainWindow


def main() -> int:
    os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")
    QCoreApplication.setApplicationName(APP_DISPLAY_NAME)
    QCoreApplication.setApplicationVersion("0.1.0")
    QCoreApplication.setOrganizationName(ORG_NAME)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)

    store = DataStore()
    window = MainWindow(store)
    window.resize(1180, 820)
    window.show()
    result = app.exec()
    store.close()
    return result

