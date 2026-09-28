"""Procedural RF Wavefield & Constellation Canvas inspired by Austensor WebGL aesthetics."""

from __future__ import annotations

import math
import os
import random

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer
from PySide6.QtGui import (
    QColor,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPaintEvent,
    QPen,
)
from PySide6.QtWidgets import QWidget

from signal_lab.gui.theme import ScientificPalette


class WaveParticle:
    """Floating constellation node."""

    def __init__(self, x: float, y: float, vx: float, vy: float, size: float, color: QColor) -> None:
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.size = size
        self.color = color
        self.alpha_phase = random.uniform(0, 2 * math.pi)

    def update(self, width: float, height: float, dt: float) -> None:
        self.x += self.vx * dt
        self.y += self.vy * dt
        self.alpha_phase += dt * 1.5

        # Wrap boundaries
        if self.x < 0:
            self.x = width
        elif self.x > width:
            self.x = 0
        if self.y < 0:
            self.y = height
        elif self.y > height:
            self.y = 0


class WavefieldCanvas(QWidget):
    """High-performance ambient RF wavefield and constellation canvas.

    Renders procedural multi-harmonic carrier waves, golden ratio spiral harmonics,
    and floating constellation particles with zero GPU memory overhead.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, True)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)

        self._time = 0.0
        self._particles: list[WaveParticle] = []
        self._num_particles = 32

        # Initialize particles
        gold_color = QColor(ScientificPalette.ACCENT_GOLD)
        cyan_color = QColor(ScientificPalette.ACCENT_CYAN)

        for _ in range(self._num_particles):
            color = gold_color if random.random() > 0.6 else cyan_color
            self._particles.append(
                WaveParticle(
                    x=random.uniform(0, 800),
                    y=random.uniform(0, 400),
                    vx=random.uniform(-15, 15),
                    vy=random.uniform(-10, 10),
                    size=random.uniform(1.5, 3.2),
                    color=color,
                )
            )

        # 30 FPS animation timer (disabled in offscreen mode to conserve test resources)
        self._is_offscreen = os.environ.get("QT_QPA_PLATFORM") == "offscreen"
        self._timer = QTimer(self)
        self._timer.setInterval(33)  # ~30 FPS
        self._timer.timeout.connect(self._on_tick)
        if not self._is_offscreen:
            self._timer.start()

    def _on_tick(self) -> None:
        self._time += 0.033
        w = max(1.0, float(self.width()))
        h = max(1.0, float(self.height()))

        for p in self._particles:
            p.update(w, h, 0.033)

        self.update()

    def paintEvent(self, event: QPaintEvent) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing, True)

        w = float(self.width())
        h = float(self.height())
        if w <= 10 or h <= 10:
            return

        mid_y = h * 0.52

        # 1. Ambient Radial Glow (Austensor golden/cyan core)
        gold_grad = QLinearGradient(0, 0, w, h)
        gold_grad.setColorAt(0.0, QColor(212, 175, 55, 18))  # Golden ratio amber tint
        gold_grad.setColorAt(0.5, QColor(0, 240, 255, 12))   # Electric cyan tint
        gold_grad.setColorAt(1.0, QColor(3, 5, 8, 0))
        painter.fillRect(QRectF(0, 0, w, h), gold_grad)

        # 2. Harmonic Carrier Wave Superposition (HF / VHF / UHF simulation)
        harmonics = [
            (0.008, 0.9, 32.0, QColor(0, 240, 255, 35), 1.2),   # Primary carrier
            (0.016, -1.3, 18.0, QColor(212, 175, 55, 30), 1.0), # Secondary phase harmonic
            (0.004, 0.5, 45.0, QColor(10, 132, 255, 20), 1.5),  # Long-range ionospheric envelope
        ]

        step = 6.0
        num_points = int(w / step) + 2

        for freq, speed, amp, color, stroke_w in harmonics:
            path = QPainterPath()
            phase = self._time * speed

            for i in range(num_points):
                x = i * step
                # Multi-frequency synthesis
                y = mid_y + amp * math.sin(x * freq + phase) * math.cos(x * 0.002 + phase * 0.3)
                if i == 0:
                    path.moveTo(x, y)
                else:
                    path.lineTo(x, y)

            pen = QPen(color, stroke_w)
            painter.setPen(pen)
            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.drawPath(path)

        # 3. Constellation Nodes & Mesh Connectors
        for i, p in enumerate(self._particles):
            # Pulsing alpha
            alpha = int(140 + 80 * math.sin(p.alpha_phase))
            node_color = QColor(p.color)
            node_color.setAlpha(max(10, min(255, alpha)))

            painter.setPen(Qt.PenStyle.NoPen)
            painter.setBrush(node_color)
            painter.drawEllipse(QPointF(p.x, p.y), p.size, p.size)

            # Draw subtle constellation links between nearby particles
            for j in range(i + 1, min(i + 4, len(self._particles))):
                other = self._particles[j]
                dx = p.x - other.x
                dy = p.y - other.y
                dist_sq = dx * dx + dy * dy
                if dist_sq < 9000:  # ~95px distance
                    link_alpha = int(35 * (1.0 - math.sqrt(dist_sq) / 95.0))
                    if link_alpha > 0:
                        link_color = QColor(ScientificPalette.BORDER_GOLD)
                        link_color.setAlpha(link_alpha)
                        painter.setPen(QPen(link_color, 0.8))
                        painter.drawLine(QPointF(p.x, p.y), QPointF(other.x, other.y))
