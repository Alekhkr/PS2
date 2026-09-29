"""Signal Profile widget displaying key physical-layer telemetry and confidence scores."""

from __future__ import annotations

from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)

from signal_lab.gui.theme import ScientificPalette, get_monospace_font, get_ui_font


class SignalProfileWidget(QFrame):
    """Dense scientific signal profile panel displaying inferred physical-layer parameters."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(
            f"""
            SignalProfileWidget {{
                background-color: {ScientificPalette.BG_SURFACE};
                border: 1px solid {ScientificPalette.BORDER_SUBTLE};
                border-radius: 4px;
            }}
            QLabel.MetricCaption {{
                color: {ScientificPalette.TEXT_MUTED};
                font-family: 'Inter', sans-serif;
                font-size: 9px;
                font-weight: 600;
                letter-spacing: 1px;
            }}
            QLabel.MetricValue {{
                color: {ScientificPalette.TEXT_PRIMARY};
                font-family: 'JetBrains Mono', monospace;
                font-size: 13px;
                font-weight: bold;
            }}
            QLabel.MetricUnit {{
                color: {ScientificPalette.TEXT_SECONDARY};
                font-family: 'JetBrains Mono', monospace;
                font-size: 10px;
            }}
            """
        )
        self._init_ui()

    def _init_ui(self) -> None:
        root_layout = QVBoxLayout(self)
        root_layout.setContentsMargins(14, 12, 14, 12)
        root_layout.setSpacing(10)

        # Header Title
        title_box = QHBoxLayout()
        title = QLabel("SIGNAL PROFILE")
        title.setFont(get_ui_font(10, get_ui_font().weight().Bold))
        title.setStyleSheet(f"color: {ScientificPalette.ACCENT_CYAN}; letter-spacing: 1.5px;")
        title_box.addWidget(title)

        title_box.addStretch()

        self.confidence_badge = QLabel("CONFIDENCE: --%")
        self.confidence_badge.setFont(get_monospace_font(9, get_monospace_font().weight().Bold))
        self.confidence_badge.setStyleSheet(
            f"color: {ScientificPalette.TEXT_SECONDARY}; background: {ScientificPalette.BG_BASE}; border: 1px solid {ScientificPalette.BORDER_SUBTLE}; border-radius: 3px; padding: 2px 6px;"
        )
        title_box.addWidget(self.confidence_badge)
        root_layout.addLayout(title_box)

        # Confidence Progress Bar
        self.conf_bar = QProgressBar()
        self.conf_bar.setFixedHeight(4)
        self.conf_bar.setRange(0, 100)
        self.conf_bar.setValue(0)
        self.conf_bar.setTextVisible(False)
        self.conf_bar.setStyleSheet(
            f"""
            QProgressBar {{
                background-color: {ScientificPalette.BG_BASE};
                border: none;
                border-radius: 2px;
            }}
            QProgressBar::chunk {{
                background-color: {ScientificPalette.ACCENT_CYAN};
                border-radius: 2px;
            }}
            """
        )
        root_layout.addWidget(self.conf_bar)

        # Metrics Grid (2 columns x 3 rows)
        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(10)

        # 1. Modulation
        self.mod_val, mod_w = self._create_metric_widget("MODULATION", "PENDING", "")
        self.mod_val.setStyleSheet(f"color: {ScientificPalette.ACCENT_CYAN};")
        grid.addWidget(mod_w, 0, 0)

        # 2. Symbol Rate
        self.baud_val, baud_w = self._create_metric_widget("SYMBOL RATE", "--", "kSym/s")
        grid.addWidget(baud_w, 0, 1)

        # 3. Occupied Bandwidth
        self.obw_val, obw_w = self._create_metric_widget("OCCUPIED BW (99%)", "--", "kHz")
        grid.addWidget(obw_w, 1, 0)

        # 4. SNR
        self.snr_val, snr_w = self._create_metric_widget("ESTIMATED SNR", "--", "dB")
        grid.addWidget(snr_w, 1, 1)

        # 5. Carrier Frequency
        self.carrier_val, carrier_w = self._create_metric_widget("CARRIER OFFSET", "--", "kHz")
        grid.addWidget(carrier_w, 2, 0)

        # 6. Synchronization Status
        self.sync_val, sync_w = self._create_metric_widget("SYNC STATUS", "UNLOCKED", "")
        self.sync_val.setStyleSheet(f"color: {ScientificPalette.TEXT_MUTED}; font-size: 11px;")
        grid.addWidget(sync_w, 2, 1)

        root_layout.addLayout(grid)

        # Evidence Summary Box
        self.evidence_frame = QFrame()
        self.evidence_frame.setStyleSheet(
            f"background-color: {ScientificPalette.BG_BASE}; border: 1px solid {ScientificPalette.BORDER_SUBTLE}; border-radius: 3px; padding: 6px;"
        )
        ev_vbox = QVBoxLayout(self.evidence_frame)
        ev_vbox.setContentsMargins(6, 6, 6, 6)
        ev_vbox.setSpacing(4)

        ev_title = QLabel("KEY EVIDENCE")
        ev_title.setFont(get_ui_font(8, get_ui_font().weight().Bold))
        ev_title.setStyleSheet(f"color: {ScientificPalette.TEXT_MUTED}; letter-spacing: 1px;")
        ev_vbox.addWidget(ev_title)

        self.evidence_label = QLabel("Awaiting automated signal analysis...")
        self.evidence_label.setFont(get_monospace_font(9))
        self.evidence_label.setStyleSheet(f"color: {ScientificPalette.TEXT_SECONDARY};")
        self.evidence_label.setWordWrap(True)
        ev_vbox.addWidget(self.evidence_label)

        root_layout.addWidget(self.evidence_frame, 1)

    def _create_metric_widget(
        self, caption_text: str, default_val: str, unit_text: str
    ) -> tuple[QLabel, QWidget]:
        w = QWidget()
        vbox = QVBoxLayout(w)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(2)

        caption = QLabel(caption_text)
        caption.setProperty("class", "MetricCaption")
        caption.setFont(get_ui_font(8, get_ui_font().weight().Bold))
        caption.setStyleSheet(f"color: {ScientificPalette.TEXT_MUTED}; letter-spacing: 0.8px;")
        vbox.addWidget(caption)

        h_val = QHBoxLayout()
        h_val.setContentsMargins(0, 0, 0, 0)
        h_val.setSpacing(4)

        val_label = QLabel(default_val)
        val_label.setFont(get_monospace_font(12, get_monospace_font().weight().Bold))
        val_label.setStyleSheet(f"color: {ScientificPalette.TEXT_PRIMARY};")
        h_val.addWidget(val_label)

        if unit_text:
            unit_label = QLabel(unit_text)
            unit_label.setFont(get_monospace_font(9))
            unit_label.setStyleSheet(f"color: {ScientificPalette.TEXT_MUTED};")
            h_val.addWidget(unit_label)

        h_val.addStretch()
        vbox.addLayout(h_val)
        return val_label, w

    def update_profile(
        self,
        modulation: str | None = None,
        symbol_rate_hz: float | None = None,
        bandwidth_hz: float | None = None,
        snr_db: float | None = None,
        carrier_offset_hz: float | None = None,
        confidence: float | None = None,
        sync_locked: bool | None = None,
        evidence_notes: list[str] | None = None,
    ) -> None:
        """Update metrics in the signal profile."""
        if modulation:
            self.mod_val.setText(modulation.upper())

        if symbol_rate_hz is not None:
            if symbol_rate_hz >= 1e6:
                self.baud_val.setText(f"{symbol_rate_hz / 1e6:.3f} MS/s")
            elif symbol_rate_hz >= 1e3:
                self.baud_val.setText(f"{symbol_rate_hz / 1e3:.2f}")
            else:
                self.baud_val.setText(f"{symbol_rate_hz:.1f} S/s")

        if bandwidth_hz is not None:
            if bandwidth_hz >= 1e6:
                self.obw_val.setText(f"{bandwidth_hz / 1e6:.3f} MHz")
            elif bandwidth_hz >= 1e3:
                self.obw_val.setText(f"{bandwidth_hz / 1e3:.1f}")
            else:
                self.obw_val.setText(f"{bandwidth_hz:.1f} Hz")

        if snr_db is not None:
            self.snr_val.setText(f"{snr_db:.1f}")

        if carrier_offset_hz is not None:
            if abs(carrier_offset_hz) >= 1e6:
                self.carrier_val.setText(f"{carrier_offset_hz / 1e6:+.3f} MHz")
            elif abs(carrier_offset_hz) >= 1e3:
                self.carrier_val.setText(f"{carrier_offset_hz / 1e3:+.2f}")
            else:
                self.carrier_val.setText(f"{carrier_offset_hz:+.1f} Hz")

        if confidence is not None:
            pct = int(confidence * 100)
            self.confidence_badge.setText(f"CONFIDENCE: {pct}%")
            self.conf_bar.setValue(pct)
            if pct >= 75:
                self.confidence_badge.setStyleSheet(
                    f"color: {ScientificPalette.ACCENT_GREEN}; background: {ScientificPalette.BG_BASE}; border: 1px solid {ScientificPalette.ACCENT_GREEN}; border-radius: 3px; padding: 2px 6px;"
                )
            elif pct >= 45:
                self.confidence_badge.setStyleSheet(
                    f"color: {ScientificPalette.ACCENT_CYAN}; background: {ScientificPalette.BG_BASE}; border: 1px solid {ScientificPalette.ACCENT_CYAN}; border-radius: 3px; padding: 2px 6px;"
                )
            else:
                self.confidence_badge.setStyleSheet(
                    f"color: {ScientificPalette.ACCENT_AMBER}; background: {ScientificPalette.BG_BASE}; border: 1px solid {ScientificPalette.ACCENT_AMBER}; border-radius: 3px; padding: 2px 6px;"
                )

        if sync_locked is not None:
            if sync_locked:
                self.sync_val.setText("LOCKED ✓")
                self.sync_val.setStyleSheet(f"color: {ScientificPalette.ACCENT_GREEN}; font-weight: bold;")
            else:
                self.sync_val.setText("SEARCHING...")
                self.sync_val.setStyleSheet(f"color: {ScientificPalette.ACCENT_AMBER};")

        if evidence_notes:
            bullet_points = "\n".join(f"• {note}" for note in evidence_notes[:4])
            self.evidence_label.setText(bullet_points)
            self.evidence_label.setStyleSheet(f"color: {ScientificPalette.TEXT_PRIMARY};")

    def reset_profile(self) -> None:
        """Reset profile to default pending state."""
        self.mod_val.setText("PENDING")
        self.baud_val.setText("--")
        self.obw_val.setText("--")
        self.snr_val.setText("--")
        self.carrier_val.setText("--")
        self.sync_val.setText("UNLOCKED")
        self.sync_val.setStyleSheet(f"color: {ScientificPalette.TEXT_MUTED};")
        self.confidence_badge.setText("CONFIDENCE: --%")
        self.conf_bar.setValue(0)
        self.evidence_label.setText("Awaiting automated signal analysis...")
