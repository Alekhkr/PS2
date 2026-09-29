"""Demodulation and synchronization analysis workspace."""

from __future__ import annotations

from typing import Any

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from signal_lab.domain.models.signal import SignalBuffer
from signal_lab.gui.plots.constellation_plot import ConstellationPlotWidget
from signal_lab.gui.theme import ScientificPalette, get_monospace_font, get_ui_font


class DemodViewWidget(QWidget):
    """Dedicated Demodulation and Phase/Timing Synchronization workspace."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._init_ui()

    def _init_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        splitter.setChildrenCollapsible(False)

        # Left: High-resolution Constellation Plot
        self.constellation_plot = ConstellationPlotWidget(self)
        splitter.addWidget(self.constellation_plot)

        # Right: Synchronization & Demodulation Diagnostics Panel
        right_container = QFrame()
        right_container.setStyleSheet(
            f"background-color: {ScientificPalette.BG_SURFACE}; border: 1px solid {ScientificPalette.BORDER_SUBTLE}; border-radius: 4px;"
        )
        r_layout = QVBoxLayout(right_container)
        r_layout.setContentsMargins(14, 12, 14, 12)
        r_layout.setSpacing(12)

        # Title
        title_box = QHBoxLayout()
        title = QLabel("DEMODULATION & SYNCHRONIZATION")
        title.setFont(get_ui_font(10, get_ui_font().weight().Bold))
        title.setStyleSheet(f"color: {ScientificPalette.ACCENT_CYAN}; letter-spacing: 1.5px;")
        title_box.addWidget(title)

        title_box.addStretch()

        self.lock_badge = QLabel("SYNC: PENDING")
        self.lock_badge.setFont(get_monospace_font(9, get_monospace_font().weight().Bold))
        self.lock_badge.setStyleSheet(
            f"color: {ScientificPalette.TEXT_MUTED}; background: {ScientificPalette.BG_BASE}; border: 1px solid {ScientificPalette.BORDER_SUBTLE}; border-radius: 3px; padding: 2px 6px;"
        )
        title_box.addWidget(self.lock_badge)
        r_layout.addLayout(title_box)

        # Metrics Grid
        grid = QGridLayout()
        grid.setHorizontalSpacing(16)
        grid.setVerticalSpacing(10)

        self.lbl_mod = self._create_card(grid, 0, 0, "MODULATION", "PENDING", "")
        self.lbl_symbols = self._create_card(grid, 0, 1, "SYMBOLS RECOVERED", "--", "")
        self.lbl_evm = self._create_card(grid, 1, 0, "RMS EVM", "--", "%")
        self.lbl_phase_err = self._create_card(grid, 1, 1, "PHASE ERROR RMS", "--", "rad")
        self.lbl_sps = self._create_card(grid, 2, 0, "ESTIMATED SPS", "--", "smp/sym")
        self.lbl_bits = self._create_card(grid, 2, 1, "DEMODULATED BITS", "--", "bits")

        r_layout.addLayout(grid)

        # Costas Loop & Timing Convergence Graph
        r_layout.addWidget(QLabel("CARRIER & TIMING ERROR RESIDUALS"))
        self.error_plot = pg.PlotWidget()
        self.error_plot.setBackground(ScientificPalette.BG_BASE)
        self.error_plot.showGrid(x=True, y=True, alpha=0.15)
        self.error_plot.setLabel("bottom", "Symbol Index", **{"font-size": "9pt"})
        self.error_plot.setLabel("left", "Error", **{"font-size": "9pt"})

        self.phase_curve = self.error_plot.plot(
            pen=pg.mkPen(ScientificPalette.ACCENT_CYAN, width=1.5), name="Phase Error"
        )
        self.timing_curve = self.error_plot.plot(
            pen=pg.mkPen(ScientificPalette.ACCENT_AMBER, width=1.2), name="Timing Error"
        )
        r_layout.addWidget(self.error_plot, 1)

        splitter.addWidget(right_container)
        splitter.setSizes([600, 500])
        layout.addWidget(splitter)

    def _create_card(
        self,
        grid: QGridLayout,
        row: int,
        col: int,
        caption: str,
        val: str,
        unit: str,
    ) -> QLabel:
        w = QWidget()
        vbox = QVBoxLayout(w)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(2)

        lbl_caption = QLabel(caption)
        lbl_caption.setFont(get_ui_font(8, get_ui_font().weight().Bold))
        lbl_caption.setStyleSheet(f"color: {ScientificPalette.TEXT_MUTED}; letter-spacing: 0.8px;")
        vbox.addWidget(lbl_caption)

        h_val = QHBoxLayout()
        h_val.setContentsMargins(0, 0, 0, 0)
        h_val.setSpacing(4)

        lbl_val = QLabel(val)
        lbl_val.setFont(get_monospace_font(12, get_monospace_font().weight().Bold))
        lbl_val.setStyleSheet(f"color: {ScientificPalette.TEXT_PRIMARY};")
        h_val.addWidget(lbl_val)

        if unit:
            lbl_u = QLabel(unit)
            lbl_u.setFont(get_monospace_font(9))
            lbl_u.setStyleSheet(f"color: {ScientificPalette.TEXT_MUTED};")
            h_val.addWidget(lbl_u)

        h_val.addStretch()
        vbox.addLayout(h_val)
        grid.addWidget(w, row, col)
        return lbl_val

    def set_signal(self, buffer: SignalBuffer) -> None:
        """Forward buffer to constellation."""
        self.constellation_plot.set_signal(buffer)

    def set_demodulation_result(self, res: Any) -> None:
        """Update metrics and error convergence curves from DemodulationResult."""
        if res is None:
            return

        if hasattr(res, "modulation"):
            self.lbl_mod.setText(str(res.modulation).upper())
        if hasattr(res, "symbols") and res.symbols is not None:
            self.lbl_symbols.setText(f"{len(res.symbols):,}")
            # Plot constellation from recovered symbols
            if len(res.symbols) > 0:
                self.constellation_plot.scatter.setData(
                    x=np.real(res.symbols[:4000]),
                    y=np.imag(res.symbols[:4000]),
                )
        if hasattr(res, "hard_bits") and res.hard_bits is not None:
            self.lbl_bits.setText(f"{len(res.hard_bits):,}")
        if hasattr(res, "evm_rms") and res.evm_rms is not None:
            self.lbl_evm.setText(f"{res.evm_rms * 100:.1f}")

        # Synchronization diagnostics
        diag = getattr(res, "diagnostics", {}) or {}
        pe = diag.get("phase_errors")
        te = diag.get("timing_errors")

        if pe is not None and len(pe) > 0:
            pe_arr = np.array(pe[:1000])
            self.phase_curve.setData(pe_arr)
            rms_pe = float(np.sqrt(np.mean(pe_arr**2)))
            self.lbl_phase_err.setText(f"{rms_pe:.3f}")
        if te is not None and len(te) > 0:
            te_arr = np.array(te[:1000])
            self.timing_curve.setData(te_arr)

        is_locked = diag.get("carrier_locked", True)
        if is_locked:
            self.lock_badge.setText("SYNC: LOCKED ✓")
            self.lock_badge.setStyleSheet(
                f"color: {ScientificPalette.ACCENT_GREEN}; background: {ScientificPalette.BG_BASE}; border: 1px solid {ScientificPalette.ACCENT_GREEN}; border-radius: 3px; padding: 2px 6px;"
            )
        else:
            self.lock_badge.setText("SYNC: SEARCHING")
            self.lock_badge.setStyleSheet(
                f"color: {ScientificPalette.ACCENT_AMBER}; background: {ScientificPalette.BG_BASE}; border: 1px solid {ScientificPalette.ACCENT_AMBER}; border-radius: 3px; padding: 2px 6px;"
            )
