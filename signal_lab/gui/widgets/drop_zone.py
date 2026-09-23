"""DropZone and Welcome Workspace widget for initial file selection."""

from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QDragEnterEvent, QDragLeaveEvent, QDropEvent
from PySide6.QtWidgets import (
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from signal_lab.domain.models.session import Session
from signal_lab.gui.theme import ScientificPalette, get_monospace_font, get_ui_font


class DropZoneWidget(QWidget):
    """Initial landing workspace for file ingestion and recent sessions."""

    file_selected = Signal(str)
    session_opened = Signal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAcceptDrops(True)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(64, 48, 64, 48)
        layout.setSpacing(32)

        # Drop Area Frame
        self.drop_frame = QFrame()
        self.drop_frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.drop_frame.setStyleSheet(
            f"""
            QFrame {{
                background-color: {ScientificPalette.BG_SURFACE};
                border: 2px dashed {ScientificPalette.BORDER_STRONG};
                border-radius: 8px;
            }}
            QFrame:hover {{
                border-color: {ScientificPalette.ACCENT_CYAN};
                background-color: {ScientificPalette.BG_CARD};
            }}
            """
        )

        drop_layout = QVBoxLayout(self.drop_frame)
        drop_layout.setContentsMargins(32, 64, 32, 64)
        drop_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        drop_layout.setSpacing(16)

        icon_lbl = QLabel("◈")
        icon_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        icon_lbl.setFont(get_monospace_font(32))
        icon_lbl.setStyleSheet(f"color: {ScientificPalette.ACCENT_CYAN};")
        drop_layout.addWidget(icon_lbl)

        title_lbl = QLabel("DROP IQ / WAV CAPTURE HERE")
        title_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_lbl.setFont(get_ui_font(14, get_ui_font().weight().Bold))
        title_lbl.setStyleSheet(f"color: {ScientificPalette.TEXT_PRIMARY}; letter-spacing: 1px;")
        drop_layout.addWidget(title_lbl)

        subtitle_lbl = QLabel("Supports WAV (PCM/Float) and Raw Binary IQ captures")
        subtitle_lbl.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle_lbl.setFont(get_ui_font(11))
        subtitle_lbl.setStyleSheet(f"color: {ScientificPalette.TEXT_SECONDARY};")
        drop_layout.addWidget(subtitle_lbl)

        btn_row = QHBoxLayout()
        btn_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.btn_browse = QPushButton("Open Capture File")
        self.btn_browse.setProperty("primary", "true")
        self.btn_browse.setFixedWidth(180)
        self.btn_browse.clicked.connect(self._on_browse_clicked)
        btn_row.addWidget(self.btn_browse)
        drop_layout.addLayout(btn_row)

        layout.addWidget(self.drop_frame)

        # Recent Sessions Area
        self.recent_box = QWidget()
        recent_layout = QVBoxLayout(self.recent_box)
        recent_layout.setContentsMargins(0, 0, 0, 0)
        recent_layout.setSpacing(8)

        recent_title = QLabel("RECENT SESSIONS")
        recent_title.setFont(get_ui_font(9, get_ui_font().weight().Bold))
        recent_title.setStyleSheet(f"color: {ScientificPalette.TEXT_MUTED}; letter-spacing: 1px;")
        recent_layout.addWidget(recent_title)

        self.recent_list = QListWidget()
        self.recent_list.setFixedHeight(140)
        self.recent_list.setStyleSheet(
            f"""
            QListWidget {{
                background-color: {ScientificPalette.BG_SURFACE};
                border: 1px solid {ScientificPalette.BORDER_SUBTLE};
                border-radius: 4px;
            }}
            QListWidget::item {{
                padding: 8px 12px;
                border-bottom: 1px solid {ScientificPalette.BORDER_SUBTLE};
            }}
            QListWidget::item:hover {{
                background-color: {ScientificPalette.BG_HOVER};
            }}
            """
        )
        self.recent_list.itemClicked.connect(self._on_recent_item_clicked)
        recent_layout.addWidget(self.recent_list)

        layout.addWidget(self.recent_box)

    def populate_recent_sessions(self, sessions: list[Session]) -> None:
        """Fill recent sessions list."""
        self.recent_list.clear()
        if not sessions:
            item = QListWidgetItem("No recent sessions")
            item.setFlags(Qt.ItemFlag.NoItemFlags)
            self.recent_list.addItem(item)
            return

        for sess in sessions:
            fname = Path(sess.input_file_path).name if sess.input_file_path else "No file"
            date_str = sess.updated_at[:19].replace("T", " ")
            item = QListWidgetItem(f"{sess.name}  —  {fname}  ({date_str} UTC)")
            item.setData(Qt.ItemDataRole.UserRole, sess.id)
            item.setFont(get_monospace_font(9))
            self.recent_list.addItem(item)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.drop_frame.setStyleSheet(
                f"""
                QFrame {{
                    background-color: {ScientificPalette.BG_CARD};
                    border: 2px solid {ScientificPalette.ACCENT_CYAN};
                    border-radius: 8px;
                }}
                """
            )

    def dragLeaveEvent(self, event: QDragLeaveEvent) -> None:
        self.drop_frame.setStyleSheet(
            f"""
            QFrame {{
                background-color: {ScientificPalette.BG_SURFACE};
                border: 2px dashed {ScientificPalette.BORDER_STRONG};
                border-radius: 8px;
            }}
            """
        )

    def dropEvent(self, event: QDropEvent) -> None:
        urls = event.mimeData().urls()
        if urls:
            path = urls[0].toLocalFile()
            if path:
                self.file_selected.emit(path)
        event.acceptProposedAction()

    def _on_browse_clicked(self) -> None:
        filepath, _ = QFileDialog.getOpenFileName(
            self,
            "Open Signal Capture",
            "",
            "Signal Files (*.wav *.wave *.iq *.bin *.raw *.dat *.sigmf-meta *.sigmf-data *.sigmf);;All Files (*.*)",
        )
        if filepath:
            self.file_selected.emit(filepath)

    def _on_recent_item_clicked(self, item: QListWidgetItem) -> None:
        session_id = item.data(Qt.ItemDataRole.UserRole)
        if session_id:
            self.session_opened.emit(session_id)
