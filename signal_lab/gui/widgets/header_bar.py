"""Header Bar widget displaying active capture telemetry and session status."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from signal_lab.gui.theme import ScientificPalette, get_monospace_font, get_ui_font


class HeaderBar(QFrame):
    """Minimal, dense scientific instrument telemetry header."""

    new_session_requested = Signal()
    auto_analyze_requested = Signal()
    export_report_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(50)
        self.setStyleSheet(
            f"""
            HeaderBar {{
                background-color: {ScientificPalette.BG_SURFACE};
                border-bottom: 1px solid {ScientificPalette.BORDER_SUBTLE};
            }}
            QPushButton#AutoAnalyzeBtn {{
                background-color: {ScientificPalette.ACCENT_CYAN};
                color: {ScientificPalette.BG_BASE};
                border: none;
                border-radius: 3px;
                padding: 5px 14px;
                font-family: 'Inter', sans-serif;
                font-size: 11px;
                font-weight: bold;
                letter-spacing: 0.5px;
            }}
            QPushButton#AutoAnalyzeBtn:hover {{
                background-color: #38bdf8;
            }}
            QPushButton#NewSessionBtn {{
                background-color: {ScientificPalette.BG_CARD};
                color: {ScientificPalette.TEXT_PRIMARY};
                border: 1px solid {ScientificPalette.BORDER_SUBTLE};
                border-radius: 3px;
                padding: 5px 12px;
                font-family: 'Inter', sans-serif;
                font-size: 11px;
            }}
            QPushButton#NewSessionBtn:hover {{
                border-color: {ScientificPalette.TEXT_MUTED};
                background-color: {ScientificPalette.BG_SURFACE};
            }}
            """
        )
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(16)

        # Brand / Title
        self.brand_label = QLabel("SIGNAL LAB")
        self.brand_label.setFont(get_ui_font(11, get_ui_font().weight().Bold))
        self.brand_label.setStyleSheet(
            f"color: {ScientificPalette.ACCENT_CYAN}; letter-spacing: 2px;"
        )
        layout.addWidget(self.brand_label)

        # Separator
        sep1 = QFrame()
        sep1.setFrameShape(QFrame.Shape.VLine)
        sep1.setStyleSheet(f"color: {ScientificPalette.BORDER_SUBTLE};")
        layout.addWidget(sep1)

        # Session ID Badge
        self.session_badge = self._create_telemetry_badge("SESSION", "SL-0001")
        layout.addWidget(self.session_badge)

        # Capture File Identifier
        self.file_badge = self._create_telemetry_badge("FILE", "NO CAPTURE LOADED")
        self.file_label = self.file_badge.val_label  # type: ignore[attr-defined]
        layout.addWidget(self.file_badge)

        # Format Badge
        self.format_badge = self._create_telemetry_badge("FORMAT", "--")
        layout.addWidget(self.format_badge)

        # Duration Badge
        self.duration_badge = self._create_telemetry_badge("DURATION", "-- s")
        layout.addWidget(self.duration_badge)

        # Telemetry: Sample Rate
        self.rate_badge = self._create_telemetry_badge("SAMPLE RATE", "-- MS/s")
        layout.addWidget(self.rate_badge)

        # Telemetry: Center Frequency
        self.freq_badge = self._create_telemetry_badge("CENTER FREQ", "-- MHz")
        layout.addWidget(self.freq_badge)

        layout.addStretch()

        # Job Status Indicator
        self.status_container = QWidget()
        status_layout = QVBoxLayout(self.status_container)
        status_layout.setContentsMargins(0, 6, 0, 6)
        status_layout.setSpacing(2)

        self.status_label = QLabel("IDLE")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.status_label.setFont(get_monospace_font(9, get_monospace_font().weight().Bold))
        self.status_label.setStyleSheet(f"color: {ScientificPalette.TEXT_SECONDARY};")
        status_layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(130)
        self.progress_bar.setFixedHeight(3)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        status_layout.addWidget(self.progress_bar)

        layout.addWidget(self.status_container)

        # Actions: Auto Analyze Button
        self.btn_auto_analyze = QPushButton("⚡ AUTO ANALYZE")
        self.btn_auto_analyze.setObjectName("AutoAnalyzeBtn")
        self.btn_auto_analyze.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_auto_analyze.clicked.connect(self.auto_analyze_requested.emit)
        layout.addWidget(self.btn_auto_analyze)

        # Actions: New Session / Open
        self.btn_new = QPushButton("New Session")
        self.btn_new.setObjectName("NewSessionBtn")
        self.btn_new.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.btn_new.clicked.connect(self.new_session_requested.emit)
        layout.addWidget(self.btn_new)

    def _create_telemetry_badge(self, label_text: str, value_text: str) -> QWidget:
        container = QWidget()
        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(0, 6, 0, 6)
        vbox.setSpacing(1)

        caption = QLabel(label_text)
        caption.setFont(get_ui_font(8))
        caption.setStyleSheet(f"color: {ScientificPalette.TEXT_MUTED}; letter-spacing: 1px;")
        vbox.addWidget(caption)

        val_label = QLabel(value_text)
        val_label.setFont(get_monospace_font(9, get_monospace_font().weight().DemiBold))
        val_label.setStyleSheet(f"color: {ScientificPalette.TEXT_PRIMARY};")
        container.val_label = val_label  # type: ignore[attr-defined]
        vbox.addWidget(val_label)
        return container

    def set_session_id(self, session_id: str) -> None:
        """Update session identifier display."""
        short_id = session_id[:8].upper() if len(session_id) > 8 else session_id.upper()
        self.session_badge.val_label.setText(f"SL-{short_id}")  # type: ignore[attr-defined]

    def set_capture_info(
        self,
        filename: str,
        sample_rate_hz: float | None = None,
        center_frequency_hz: float | None = None,
        source_format: str | None = None,
        duration_s: float | None = None,
    ) -> None:
        """Update header with capture properties."""
        self.file_label.setText(filename)

        if source_format:
            self.format_badge.val_label.setText(source_format.upper())  # type: ignore[attr-defined]
        else:
            self.format_badge.val_label.setText("--")  # type: ignore[attr-defined]

        if duration_s is not None:
            if duration_s >= 60.0:
                self.duration_badge.val_label.setText(f"{duration_s / 60.0:.1f} min")  # type: ignore[attr-defined]
            elif duration_s >= 1.0:
                self.duration_badge.val_label.setText(f"{duration_s:.2f} s")  # type: ignore[attr-defined]
            else:
                self.duration_badge.val_label.setText(f"{duration_s * 1e3:.1f} ms")  # type: ignore[attr-defined]
        else:
            self.duration_badge.val_label.setText("-- s")  # type: ignore[attr-defined]

        if sample_rate_hz is not None:
            if sample_rate_hz >= 1e6:
                rate_str = f"{sample_rate_hz / 1e6:.3f} MS/s"
            elif sample_rate_hz >= 1e3:
                rate_str = f"{sample_rate_hz / 1e3:.3f} kS/s"
            else:
                rate_str = f"{sample_rate_hz:.1f} S/s"
        else:
            rate_str = "UNKNOWN"
        self.rate_badge.val_label.setText(rate_str)  # type: ignore[attr-defined]

        if center_frequency_hz is not None:
            if center_frequency_hz >= 1e6:
                freq_str = f"{center_frequency_hz / 1e6:.3f} MHz"
            elif center_frequency_hz >= 1e3:
                freq_str = f"{center_frequency_hz / 1e3:.3f} kHz"
            else:
                freq_str = f"{center_frequency_hz:.1f} Hz"
        else:
            freq_str = "UNKNOWN"
        self.freq_badge.val_label.setText(freq_str)  # type: ignore[attr-defined]

    def set_job_status(self, text: str, progress: float = 0.0) -> None:
        """Update live status message and progress percentage (0.0 - 1.0)."""
        self.status_label.setText(text.upper())
        pct = int(progress * 100)
        self.progress_bar.setValue(pct)
        if 0 < pct < 100:
            self.status_label.setStyleSheet(f"color: {ScientificPalette.ACCENT_CYAN};")
        elif pct == 100 or "COMPLETE" in text.upper() or "READY" in text.upper():
            self.status_label.setStyleSheet(f"color: {ScientificPalette.ACCENT_GREEN};")
        elif "FAIL" in text.upper() or "ERROR" in text.upper():
            self.status_label.setStyleSheet(f"color: {ScientificPalette.ACCENT_RED};")
        else:
            self.status_label.setStyleSheet(f"color: {ScientificPalette.TEXT_SECONDARY};")
