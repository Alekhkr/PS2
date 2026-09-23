"""Integration tests for PyQtGraph scientific instruments and synchronized selection."""

import os

import pytest

from signal_lab.domain.models.signal import SignalBuffer, SignalSegment
from signal_lab.gui.plots.constellation_plot import ConstellationPlotWidget
from signal_lab.gui.plots.spectrum_plot import SpectrumPlotWidget
from signal_lab.gui.plots.waterfall_plot import WaterfallPlotWidget
from signal_lab.gui.plots.waveform_plot import WaveformPlotWidget
from signal_lab.gui.widgets.analysis_workspace import AnalysisWorkspaceWidget


@pytest.fixture(autouse=True)
def configure_qt_offscreen() -> None:
    """Ensure tests run in offscreen mode."""
    os.environ["QT_QPA_PLATFORM"] = "offscreen"


def test_spectrum_plot(qtbot, sample_signal_buffer: SignalBuffer) -> None:
    """Verify Welch PSD computation and peak detection in SpectrumPlotWidget."""
    plot = SpectrumPlotWidget()
    qtbot.addWidget(plot)

    plot.set_signal(sample_signal_buffer)
    x_data, y_data = plot.spectrum_curve.getData()
    assert len(x_data) > 0
    assert len(y_data) > 0
    assert len(plot.peak_scatter.data) == 1


def test_waveform_plot(qtbot, sample_signal_buffer: SignalBuffer) -> None:
    """Verify time-domain I and Q curves in WaveformPlotWidget."""
    plot = WaveformPlotWidget()
    qtbot.addWidget(plot)

    plot.set_signal(sample_signal_buffer)
    t_i, i_data = plot.i_curve.getData()
    _t_q, q_data = plot.q_curve.getData()
    assert len(t_i) > 0
    assert len(i_data) > 0
    assert len(q_data) == len(i_data)


def test_constellation_plot(qtbot, sample_signal_buffer: SignalBuffer) -> None:
    """Verify constellation scatter plot in ConstellationPlotWidget."""
    plot = ConstellationPlotWidget()
    qtbot.addWidget(plot)

    plot.set_signal(sample_signal_buffer)
    assert len(plot.scatter.data) > 0


def test_waterfall_plot_and_region(qtbot, sample_signal_buffer: SignalBuffer) -> None:
    """Verify 2D spectrogram and region selection emission in WaterfallPlotWidget."""
    plot = WaterfallPlotWidget()
    qtbot.addWidget(plot)

    plot.set_signal(sample_signal_buffer)
    assert plot.img_item.image is not None
    assert plot.region.isVisible()

    # Test region selection signal
    with qtbot.waitSignal(plot.region_selected, timeout=1000) as blocker:
        plot.region.setRegion([0.002, 0.006])
    assert blocker.args == [0.002, 0.006]


def test_synchronized_selection_in_workspace(qtbot, sample_signal_buffer: SignalBuffer) -> None:
    """Verify that moving the waterfall region synchronizes spectrum and constellation in workspace."""
    workspace = AnalysisWorkspaceWidget()
    qtbot.addWidget(workspace)

    workspace.set_signal_buffer(sample_signal_buffer)

    # Listen for segment selection emission
    selected_segments: list[SignalSegment] = []
    workspace.segment_selected.connect(selected_segments.append)

    # Trigger region change on waterfall
    workspace.waterfall_plot.region.setRegion([0.003, 0.007])

    assert len(selected_segments) == 1
    seg = selected_segments[0]
    assert pytest.approx(seg.start_time_s, abs=1e-4) == 0.003
    assert pytest.approx(seg.duration_s, abs=1e-4) == 0.004
    assert seg.start_sample == 3000
    assert seg.end_sample == 7000
