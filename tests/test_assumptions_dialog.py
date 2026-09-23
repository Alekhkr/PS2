"""Unit tests for AssumptionsDialog."""

from __future__ import annotations

import numpy as np
import pytest

from signal_lab.domain.models.signal import SignalBuffer
from signal_lab.gui.widgets.assumptions_dialog import AssumptionsDialog


@pytest.fixture
def dummy_buffer() -> SignalBuffer:
    t = np.arange(1024)
    samples = (np.cos(2 * np.pi * 0.1 * t) + 1j * np.sin(2 * np.pi * 0.1 * t)).astype(np.complex64)
    return SignalBuffer(samples=samples, sample_rate_hz=None, center_frequency_hz=None)


def test_assumptions_dialog_init(qtbot, dummy_buffer: SignalBuffer) -> None:
    dialog = AssumptionsDialog(dummy_buffer)
    qtbot.addWidget(dialog)

    assert dialog.spin_rate.value() == 2_048_000.0
    assert dialog.spin_fc.value() == 0.0


def test_assumptions_dialog_preset_change(qtbot, dummy_buffer: SignalBuffer) -> None:
    dialog = AssumptionsDialog(dummy_buffer)
    qtbot.addWidget(dialog)

    # Change to 20.0 MHz preset (index 7)
    dialog.combo_presets.setCurrentIndex(7)
    assert dialog.spin_rate.value() == 20_000_000.0


def test_assumptions_dialog_apply(qtbot, dummy_buffer: SignalBuffer) -> None:
    dialog = AssumptionsDialog(dummy_buffer)
    qtbot.addWidget(dialog)

    dialog.spin_rate.setValue(10_000_000.0)
    dialog.spin_fc.setValue(433_920_000.0)

    with qtbot.waitSignal(dialog.assumptions_applied, timeout=1000):
        dialog._on_apply()

    assert dummy_buffer.sample_rate_hz == 10_000_000.0
    assert dummy_buffer.center_frequency_hz == 433_920_000.0

    evidences = dialog.get_parameter_evidences()
    assert len(evidences) == 2
    assert evidences[0].name == "sample_rate"
    assert evidences[0].value == 10_000_000.0
    assert evidences[1].name == "center_frequency"
    assert evidences[1].value == 433_920_000.0
