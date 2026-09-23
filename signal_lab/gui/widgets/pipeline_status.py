"""Pipeline Status breadcrumb widget displaying stage execution progression."""

from __future__ import annotations

from PySide6.QtWidgets import QFrame, QHBoxLayout, QLabel, QWidget

from signal_lab.gui.theme import ScientificPalette, get_monospace_font, get_ui_font


class PipelineStatusWidget(QFrame):
    """Bottom status bar indicating execution state across DSP pipeline stages."""

    STAGES = ("Detect", "Estimate", "Sync", "Demod", "Interleave", "FEC", "Correlate")

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedHeight(32)
        self.setStyleSheet(
            f"""
            PipelineStatusWidget {{
                background-color: {ScientificPalette.BG_SURFACE};
                border-top: 1px solid {ScientificPalette.BORDER_SUBTLE};
            }}
            """
        )
        self._stage_labels: dict[str, QLabel] = {}
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 0, 16, 0)
        layout.setSpacing(16)

        prefix = QLabel("PIPELINE:")
        prefix.setFont(get_ui_font(9, get_ui_font().weight().Bold))
        prefix.setStyleSheet(f"color: {ScientificPalette.TEXT_MUTED}; letter-spacing: 1px;")
        layout.addWidget(prefix)

        for stage in self.STAGES:
            lbl = QLabel(f"{stage} ○")
            lbl.setFont(get_monospace_font(9))
            lbl.setStyleSheet(f"color: {ScientificPalette.TEXT_MUTED};")
            self._stage_labels[stage.lower()] = lbl
            layout.addWidget(lbl)

        layout.addStretch()

        self.engine_mode_label = QLabel("HYBRID DETERMINISTIC DSP + ML")
        self.engine_mode_label.setFont(get_monospace_font(8))
        self.engine_mode_label.setStyleSheet(f"color: {ScientificPalette.TEXT_MUTED};")
        layout.addWidget(self.engine_mode_label)

    def set_stage_status(self, stage_name: str, status: str) -> None:
        """Update a stage's status display.

        status can be: 'pending' (○), 'running' (●), 'done' (✓), 'failed' (✗)
        """
        key = stage_name.lower()
        if key not in self._stage_labels:
            return

        lbl = self._stage_labels[key]
        stage_title = stage_name.capitalize()

        if status == "running":
            lbl.setText(f"{stage_title} ●")
            lbl.setStyleSheet(f"color: {ScientificPalette.ACCENT_CYAN}; font-weight: bold;")
        elif status == "done":
            lbl.setText(f"{stage_title} ✓")
            lbl.setStyleSheet(f"color: {ScientificPalette.ACCENT_GREEN};")
        elif status == "failed":
            lbl.setText(f"{stage_title} ✗")
            lbl.setStyleSheet(f"color: {ScientificPalette.ACCENT_RED};")
        else:
            lbl.setText(f"{stage_title} ○")
            lbl.setStyleSheet(f"color: {ScientificPalette.TEXT_MUTED};")

    def reset_all(self) -> None:
        """Reset all stages to pending."""
        for stage in self.STAGES:
            self.set_stage_status(stage, "pending")
