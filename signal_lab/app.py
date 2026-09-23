"""Application entry point and desktop lifecycle manager."""

from __future__ import annotations

import logging
import os
import signal
import sys

from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

from signal_lab.gui.main_window import MainWindow
from signal_lab.services.session_service import SessionService
from signal_lab.storage.database import DatabaseManager
from signal_lab.storage.repository import SessionRepository


def setup_logging() -> None:
    """Initialize structured logging."""
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    logging.basicConfig(level=logging.INFO, format=log_format)


def create_app() -> tuple[QApplication, MainWindow]:
    """Create and configure the Qt Application and MainWindow."""
    setup_logging()

    # Qt attributes
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

    # Clean Ctrl+C handling
    signal.signal(signal.SIGINT, lambda *args: QApplication.quit())

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    # Periodic timer to allow Python signal handler to run on event loop
    timer = QTimer()
    timer.timeout.connect(lambda: None)
    timer.start(250)
    app._sigint_timer = timer  # type: ignore[attr-defined]

    app.setApplicationName("Signal Lab")
    app.setOrganizationName("SignalLab")
    app.setApplicationVersion("0.1.0")

    # Storage & Services
    db_manager = DatabaseManager()
    repository = SessionRepository(db_manager)
    session_service = SessionService(repository)

    window = MainWindow(session_service)
    return app, window


def main() -> int:
    """Main CLI entry point."""
    app, window = create_app()
    window.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
