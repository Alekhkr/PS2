"""Pipeline Status breadcrumb widget displaying stage execution progression."""

from __future__ import annotations

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton, QWidget

from signal_lab.gui.theme import ScientificPalette, get_monospace_font, get_ui_font


class PipelineStatusWidget(QFrame):
    """Bottom status bar indicating execution state across DSP pipeline stages."""

    stage_clicked = Signal(str)  # stage_name

    STAGES = (
        "Detect",
        "Estimate",
        "Classify",
        "Synchronize",
        "Demodulate",
        "Interleave",
        "FEC",
        "Correlate",
    )

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(34)
        self.setStyleSheet(
            f"""
            PipelineStatusWidget {{
                background-color: {ScientificPalette.BG_SURFACE};
                border-top: 1px solid {ScientificPalette.BORDER_SUBTLE};
            }}
            QPushButton {{
                background-color: transparent;
                border: none;
                padding: 4px 8px;
                border-radius: 3px;
                color: {ScientificPalette.TEXT_MUTED};
                font-family: 'JetBrains Mono', monospace;
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {ScientificPalette.BG_CARD};
                color: {ScientificPalette.TEXT_PRIMARY};
            }}
            """
        )
        self._stage_buttons: dict[str, QPushButton] = {}
        self._stage_labels = self._stage_buttons
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(12)

        prefix = QLabel("PIPELINE:")
        prefix.setFont(get_ui_font(9, get_ui_font().weight().Bold))
        prefix.setStyleSheet(f"color: {ScientificPalette.TEXT_MUTED}; letter-spacing: 1px;")
        layout.addWidget(prefix)

        for stage in self.STAGES:
            btn = QPushButton(f"{stage} —")
            btn.setFocusPolicy(Qt.FocusPolicy.NoFocus)
            btn.setFont(get_monospace_font(9))
            btn.clicked.connect(lambda checked=False, s=stage: self.stage_clicked.emit(s))
            self._stage_buttons[stage.lower()] = btn
            layout.addWidget(btn)

        # Aliases for backwards compatibility with tests and callers
        self._stage_labels["sync"] = self._stage_buttons["synchronize"]
        self._stage_labels["demod"] = self._stage_buttons["demodulate"]

        layout.addStretch()

        self.engine_mode_label = QLabel("OFFLINE DETERMINISTIC DSP + NEURAL HYBRID")
        self.engine_mode_label.setFont(get_monospace_font(8))
        self.engine_mode_label.setStyleSheet(f"color: {ScientificPalette.TEXT_MUTED};")
        layout.addWidget(self.engine_mode_label)

    def set_stage_status(self, stage_name: str, status: str) -> None:
        """Update a stage's status display.

        status can be: 'pending' (—), 'running' (●), 'done' (✓), 'failed' (✗), 'unsupported' (—)
        """
        key = stage_name.lower()
        if key not in self._stage_buttons:
            # Map aliases
            alias_map = {"sync": "synchronize", "demod": "demodulate"}
            key = alias_map.get(key, key)
            if key not in self._stage_buttons:
                return

        btn = self._stage_buttons[key]
        stage_title = key.capitalize()

        if status == "running":
            btn.setText(f"{stage_title} ●")
            btn.setStyleSheet(f"color: {ScientificPalette.ACCENT_CYAN}; font-weight: bold;")
        elif status == "done":
            btn.setText(f"{stage_title} ✓")
            btn.setStyleSheet(f"color: {ScientificPalette.ACCENT_GREEN}; font-weight: bold;")
        elif status == "failed":
            btn.setText(f"{stage_title} ✗")
            btn.setStyleSheet(f"color: {ScientificPalette.ACCENT_RED};")
        elif status == "unsupported":
            btn.setText(f"{stage_title} —")
            btn.setStyleSheet(f"color: {ScientificPalette.TEXT_MUTED};")
        else:
            btn.setText(f"{stage_title} ○")
            btn.setStyleSheet(f"color: {ScientificPalette.TEXT_MUTED};")

    def reset_all(self) -> None:
        """Reset all stages to unverified."""
        for stage in self.STAGES:
            self.set_stage_status(stage, "pending")
