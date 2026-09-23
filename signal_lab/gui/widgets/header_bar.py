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
    export_report_requested = Signal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(48)
        self.setStyleSheet(
            f"""
            HeaderBar {{
                background-color: {ScientificPalette.BG_SURFACE};
                border-bottom: 1px solid {ScientificPalette.BORDER_SUBTLE};
            }}
            """
        )
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(20)

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

        # Capture File Identifier
        self.file_label = QLabel("NO CAPTURE LOADED")
        self.file_label.setFont(get_monospace_font(10))
        self.file_label.setStyleSheet(f"color: {ScientificPalette.TEXT_PRIMARY}; font-weight: 600;")
        layout.addWidget(self.file_label)

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
        status_layout.setContentsMargins(0, 8, 0, 8)
        status_layout.setSpacing(2)

        self.status_label = QLabel("IDLE")
        self.status_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.status_label.setFont(get_monospace_font(9))
        self.status_label.setStyleSheet(f"color: {ScientificPalette.TEXT_SECONDARY};")
        status_layout.addWidget(self.status_label)

        self.progress_bar = QProgressBar()
        self.progress_bar.setFixedWidth(140)
        self.progress_bar.setFixedHeight(3)
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(False)
        status_layout.addWidget(self.progress_bar)

        layout.addWidget(self.status_container)

        # Actions: New Session / Open
        self.btn_new = QPushButton("New Session")
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
        val_label.setFont(get_monospace_font(10))
        val_label.setStyleSheet(f"color: {ScientificPalette.TEXT_PRIMARY};")
        container.val_label = val_label  # type: ignore[attr-defined]
        vbox.addWidget(val_label)
        return container

    def set_capture_info(
        self,
        filename: str,
        sample_rate_hz: float | None = None,
        center_frequency_hz: float | None = None,
    ) -> None:
        """Update header with capture properties."""
        self.file_label.setText(filename)

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
        if pct > 0 and pct < 100:
            self.status_label.setStyleSheet(f"color: {ScientificPalette.ACCENT_CYAN};")
        elif pct == 100:
            self.status_label.setStyleSheet(f"color: {ScientificPalette.ACCENT_GREEN};")
        else:
            self.status_label.setStyleSheet(f"color: {ScientificPalette.TEXT_SECONDARY};")
