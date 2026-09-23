"""Waterfall (Spectrogram) 2D time-frequency visualization widget with region selector."""

from __future__ import annotations

import numpy as np
import pyqtgraph as pg
from PySide6.QtCore import Signal
from scipy import signal

from signal_lab.domain.models.signal import SignalBuffer
from signal_lab.gui.plots.base_plot import style_plot_widget
from signal_lab.gui.theme import ScientificPalette


class WaterfallPlotWidget(pg.PlotWidget):
    """2D time-frequency heatmap with interactive region selection for synchronized analysis."""

    region_selected = Signal(float, float)  # Emits (start_time_s, end_time_s)

    def __init__(self, parent: pg.QtWidgets.QWidget | None = None) -> None:
        super().__init__(parent)
        style_plot_widget(self, title="WATERFALL / SPECTROGRAM")
        self.setLabel("left", "Time", units="s")
        self.setLabel("bottom", "Frequency", units="Hz")

        self.img_item = pg.ImageItem()
        self.addItem(self.img_item)

        # Apply viridis colormap
        colormap = pg.colormap.get("viridis")
        self.img_item.setColorMap(colormap)

        # Interactive Linear Region Selector along Time axis (Y axis)
        self.region = pg.LinearRegionItem(
            orientation=pg.LinearRegionItem.Horizontal,
            brush=pg.mkBrush(color=(0, 229, 255, 40)),
            pen=pg.mkPen(color=ScientificPalette.ACCENT_CYAN, width=1.5),
        )
        self.region.sigRegionChanged.connect(self._on_region_changed)
        self.addItem(self.region)
        self.region.setVisible(False)

        self._current_buffer: SignalBuffer | None = None

    def set_signal(self, buffer: SignalBuffer, nperseg: int = 512) -> None:
        """Compute and render STFT spectrogram."""
        self._current_buffer = buffer
        if buffer.num_samples == 0:
            self.clear_waterfall()
            return

        fs = buffer.sample_rate_hz or 1.0
        nperseg = min(nperseg, max(64, buffer.num_samples // 10))
        noverlap = nperseg // 2

        freqs, times, sxx = signal.spectrogram(
            buffer.samples,
            fs=fs,
            window="hann",
            nperseg=nperseg,
            noverlap=noverlap,
            return_onesided=False,
            scaling="density",
            mode="psd",
        )

        # Shift frequencies so 0 or center is centered
        freqs = np.fft.fftshift(freqs)
        sxx = np.fft.fftshift(sxx, axes=0)

        if buffer.center_frequency_hz is not None:
            freqs += buffer.center_frequency_hz

        # Convert to dBFS
        sxx_db = 10 * np.log10(sxx + 1e-15)
        # Transpose for ImageItem coordinate system: x=freqs, y=times
        img_data = sxx_db.T

        # Set image rect bounding coordinates
        f_min, f_max = float(freqs[0]), float(freqs[-1])
        t_min, t_max = float(times[0]), float(times[-1])
        self.img_item.setImage(img_data)
        self.img_item.setRect(pg.QtCore.QRectF(f_min, t_min, f_max - f_min, t_max - t_min))

        # Initialize region selector
        self.region.setBounds([t_min, t_max])
        initial_span = min(0.005, (t_max - t_min) * 0.25)
        self.region.setRegion([t_min, t_min + initial_span])
        self.region.setVisible(True)

    def _on_region_changed(self) -> None:
        """Notify listeners when user drags or resizes the time region selector."""
        start_t, end_t = self.region.getRegion()
        self.region_selected.emit(start_t, end_t)

    def set_region(self, start_t: float, end_t: float) -> None:
        """Programmatically move region selector and trigger updates."""
        self.region.setRegion([start_t, end_t])
        self._on_region_changed()

    def clear_waterfall(self) -> None:
        self.img_item.clear()
        self.region.setVisible(False)
