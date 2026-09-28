"""Unit tests for Austensor-inspired aesthetic components: WavefieldCanvas, ExperimentDock, Dossier."""

from __future__ import annotations

from signal_lab.gui.widgets.audio_player import AudioPlayerWidget
from signal_lab.gui.widgets.dossier_dialog import ScientificDossierDialog
from signal_lab.gui.widgets.drop_zone import DropZoneWidget
from signal_lab.gui.widgets.experiment_dock import ExperimentDock
from signal_lab.gui.widgets.wavefield_canvas import WavefieldCanvas


def test_wavefield_canvas_init_and_render(qtbot) -> None:
    """Verify procedural wavefield canvas initializes and renders without error."""
    canvas = WavefieldCanvas()
    qtbot.addWidget(canvas)
    canvas.resize(600, 300)
    canvas.show()

    # Trigger tick and paintEvent
    canvas._on_tick()
    canvas.repaint()
    assert len(canvas._particles) > 0


def test_experiment_dock_signals(qtbot) -> None:
    """Verify experiment dock emits experiment_selected and dossier_requested signals."""
    dock = ExperimentDock()
    qtbot.addWidget(dock)

    received_experiments: list[str] = []
    dock.experiment_selected.connect(received_experiments.append)

    dossier_requested = []
    dock.dossier_requested.connect(lambda: dossier_requested.append(True))

    # Click first experiment button
    btn_01 = dock.findChildren(dock.btn_dossier.__class__)[1]  # first experiment pill
    btn_01.click()
    assert len(received_experiments) == 1
    assert "data/" in received_experiments[0] or "N6GN" in received_experiments[0]

    # Click dossier button
    dock.btn_dossier.click()
    assert len(dossier_requested) == 1


def test_scientific_dossier_dialog(qtbot) -> None:
    """Verify scientific dossier dialog launches and terminates cleanly in headless mode."""
    dialog = ScientificDossierDialog()
    qtbot.addWidget(dialog)
    res = dialog.exec()
    assert res == 1


def test_drop_zone_with_austensor_widgets(qtbot) -> None:
    """Verify DropZoneWidget integrates ExperimentDock, WavefieldCanvas, and dossier trigger."""
    drop_zone = DropZoneWidget()
    qtbot.addWidget(drop_zone)
    drop_zone.resize(1024, 768)
    drop_zone.show()

    assert drop_zone.wave_canvas is not None
    assert drop_zone.experiment_dock is not None

    selected_files = []
    drop_zone.file_selected.connect(selected_files.append)

    # Trigger experiment from dock
    drop_zone.experiment_dock.experiment_selected.emit("/path/to/test.wav")
    assert selected_files == ["/path/to/test.wav"]

    # Trigger dossier
    drop_zone._open_dossier()


def test_audio_player_widget(qtbot) -> None:
    """Verify audio player widget sets data and toggles playback signals."""
    import numpy as np
    player = AudioPlayerWidget()
    qtbot.addWidget(player)

    started = []
    stopped = []
    player.playback_started.connect(lambda: started.append(True))
    player.playback_stopped.connect(lambda: stopped.append(True))

    dummy_audio = np.sin(2 * np.pi * 440 * np.linspace(0, 1, 48000)).astype(np.float32)
    player.set_audio_data(dummy_audio, 48000.0)
    assert "48.0 kHz" in player.info_lbl.text()

    player._toggle_playback()
    assert len(started) == 1
    assert player._is_playing is True

    player._toggle_playback()
    assert len(stopped) == 1
    assert player._is_playing is False

