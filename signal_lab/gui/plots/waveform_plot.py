"""Time-domain waveform visualizer widget."""

from __future__ import annotations

import numpy as np
import pyqtgraph as pg

from signal_lab.domain.models.signal import SignalBuffer
from signal_lab.gui.plots.base_plot import style_plot_widget
from signal_lab.gui.theme import ScientificPalette


class WaveformPlotWidget(pg.PlotWidget):
    """Displays I/Q time-domain waveforms with real/imag components."""

    def __init__(self, parent: pg.QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        style_plot_widget(self, title="TIME WAVEFORM")
        self.setLabel("left", "Amplitude", units="V")
        self.setLabel("bottom", "Time", units="s")

        self.i_curve = self.plot(
            pen=pg.mkPen(color=ScientificPalette.ACCENT_CYAN, width=1.0),
            name="I (In-phase)",
        )
        self.q_curve = self.plot(
            pen=pg.mkPen(color=ScientificPalette.ACCENT_BLUE, width=1.0),
            name="Q (Quadrature)",
        )

    def set_signal(self, buffer: SignalBuffer, max_points: int = 5000) -> None:
        """Render decimated time-domain I and Q curves."""
        if buffer.num_samples == 0:
            self.clear_waveform()
            return

        fs = buffer.sample_rate_hz or 1.0
        n_samples = buffer.num_samples

        if n_samples > max_points:
            step = n_samples // max_points
            indices = np.arange(0, n_samples, step)
            samples = buffer.samples[indices]
            t = indices / fs
        else:
            samples = buffer.samples
            t = np.arange(n_samples) / fs

        if buffer.start_time is not None:
            t += buffer.start_time

        self.i_curve.setData(t, np.real(samples))
        self.q_curve.setData(t, np.imag(samples))

    def clear_waveform(self) -> None:
        self.i_curve.setData([], [])
        self.q_curve.setData([], [])
