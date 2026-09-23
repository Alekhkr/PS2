"""Application entry point and desktop lifecycle manager."""

from __future__ import annotations

import logging
import os
import sys

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

    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

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
