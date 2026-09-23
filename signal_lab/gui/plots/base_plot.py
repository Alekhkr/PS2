"""Base styling and configuration for PyQtGraph scientific instruments."""

from __future__ import annotations

import pyqtgraph as pg
from pyqtgraph import PlotWidget

from signal_lab.gui.theme import ScientificPalette


def configure_pyqtgraph_defaults() -> None:
    """Applies global dark scientific palette to all PyQtGraph components."""
    pg.setConfigOption("background", ScientificPalette.BG_BASE)
    pg.setConfigOption("foreground", ScientificPalette.TEXT_SECONDARY)
    pg.setConfigOption("antialias", True)


def style_plot_widget(widget: PlotWidget, title: str | None = None) -> None:
    """Styles a PlotWidget with dark borders, subtle grid, and clean axis labels."""
    widget.setBackground(ScientificPalette.BG_BASE)
    widget.showGrid(x=True, y=True, alpha=0.15)
    widget.getPlotItem().setMenuEnabled(False)  # Remove cluttered default context menu

    if title:
        widget.setTitle(
            f"<span style='color: {ScientificPalette.TEXT_SECONDARY}; font-size: 11px; font-weight: 600; letter-spacing: 1px;'>{title}</span>"
        )

    # Style axes
    for axis_name in ("left", "bottom"):
        axis = widget.getPlotItem().getAxis(axis_name)
        axis.setPen(pg.mkPen(color=ScientificPalette.BORDER_SUBTLE, width=1))
        axis.setTextPen(pg.mkPen(color=ScientificPalette.TEXT_MUTED))
