"""Unit tests for BitstreamViewer widget."""

from __future__ import annotations

import numpy as np
import pytest

from signal_lab.correlation.correlator import STANDARD_SYNC_WORDS
from signal_lab.gui.widgets.bitstream_viewer import BitstreamViewer


def test_bitstream_viewer_render_and_stats(qtbot) -> None:
    viewer = BitstreamViewer()
    qtbot.addWidget(viewer)

    # 128 bytes of data = 1024 bits
    bits = np.random.randint(0, 2, size=1024, dtype=np.uint8)
    viewer.set_bitstream(bits, sample_rate_hz=1_000_000.0, sps=4, bits_per_symbol=2)

    assert "1,024 bits" in viewer.lbl_stats.text()
    assert "128 bytes" in viewer.lbl_stats.text()
    assert viewer.table.rowCount() == 8  # 128 bytes / 16 bytes per row = 8 rows


def test_bitstream_viewer_sync_detection(qtbot) -> None:
    viewer = BitstreamViewer()
    qtbot.addWidget(viewer)

    # Insert Barker 13 at start of bitstream
    barker_13 = np.array(STANDARD_SYNC_WORDS["Barker_13"], dtype=np.uint8)
    rest = np.zeros(256, dtype=np.uint8)
    bits = np.concatenate([barker_13, rest])

    viewer.set_bitstream(bits)
    # Row 0 should have Barker-13 detected annotation
    item_annot = viewer.table.item(0, 3)
    assert item_annot is not None
    assert "Barker-13" in item_annot.text()


def test_bitstream_viewer_navigation_signals(qtbot) -> None:
    viewer = BitstreamViewer()
    qtbot.addWidget(viewer)

    bits = np.zeros(1024, dtype=np.uint8)
    viewer.set_bitstream(bits, sample_rate_hz=2_000_000.0, sps=4, bits_per_symbol=2)

    # Clicking row 1 (16 bytes = 128 bits):
    # 128 bits / 2 bits_per_symbol = 64 symbols
    # 64 symbols * 4 sps = 256 samples
    # 256 samples / 2,000,000 Hz = 0.000128 s
    item = viewer.table.item(1, 0)
    assert item is not None

    with (
        qtbot.waitSignal(viewer.sample_navigated, timeout=1000) as blocker_sample,
        qtbot.waitSignal(viewer.time_navigated, timeout=1000) as blocker_time,
    ):
        viewer._on_item_clicked(item)

    assert blocker_sample.args[0] == 256
    assert blocker_time.args[0] == pytest.approx(0.000128, rel=1e-3)
