"""Constellation diagram (I vs Q phase plane) visualization widget."""

from __future__ import annotations

import numpy as np
import pyqtgraph as pg

from signal_lab.domain.models.signal import SignalBuffer
from signal_lab.gui.plots.base_plot import style_plot_widget
from signal_lab.gui.theme import ScientificPalette


class ConstellationPlotWidget(pg.PlotWidget):
    """Complex plane scatter plot showing In-Phase vs Quadrature constellation points."""

    def __init__(self, parent: pg.QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        style_plot_widget(self, title="CONSTELLATION")
        self.setLabel("left", "Quadrature (Q)")
        self.setLabel("bottom", "In-phase (I)")
        self.setAspectLocked(True)

        # Reference crosshair axes
        self.cross_h = pg.InfiniteLine(
            pos=0,
            angle=0,
            pen=pg.mkPen(
                color=ScientificPalette.BORDER_STRONG, width=1, style=pg.QtCore.Qt.PenStyle.DashLine
            ),
        )
        self.cross_v = pg.InfiniteLine(
            pos=0,
            angle=90,
            pen=pg.mkPen(
                color=ScientificPalette.BORDER_STRONG, width=1, style=pg.QtCore.Qt.PenStyle.DashLine
            ),
        )
        self.addItem(self.cross_h)
        self.addItem(self.cross_v)

        # Scatter plot for constellation points
        self.scatter = pg.ScatterPlotItem(
            size=4,
            pen=pg.mkPen(None),
            brush=pg.mkBrush(color=(0, 229, 255, 160)),  # Electric cyan with subtle transparency
        )
        self.addItem(self.scatter)

    def set_signal(self, buffer: SignalBuffer, max_points: int = 4000) -> None:
        """Render constellation points from complex samples."""
        if buffer.num_samples == 0:
            self.clear_constellation()
            return

        samples = buffer.samples
        if len(samples) > max_points:
            # Random or uniform decimation
            step = len(samples) // max_points
            samples = samples[::step]

        i_pts = np.real(samples)
        q_pts = np.imag(samples)

        # Normalize coordinates so unit power fits within [-1.5, 1.5]
        scale = np.max(np.abs(samples))
        if scale > 1e-6:
            i_pts = i_pts / scale
            q_pts = q_pts / scale

        self.scatter.setData(x=i_pts, y=q_pts)
        self.setRange(xRange=[-1.5, 1.5], yRange=[-1.5, 1.5], padding=0.05)

    def clear_constellation(self) -> None:
        self.scatter.setData([], [])
