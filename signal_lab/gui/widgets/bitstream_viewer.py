"""Interactive Bitstream & Protocol Frame Inspector UI.

Features:
- Hex, Binary, and ASCII view modes with synchronized offsets.
- Automatic color highlighting of detected preambles (Barker, CCSDS) and frame boundaries.
- Interactive click-to-waveform navigation (repositioning time instruments on bit click).
- Real-time pattern search across binary and hex representations.
"""

from __future__ import annotations

import numpy as np
from PySide6.QtCore import Signal
from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from signal_lab.correlation.correlator import STANDARD_SYNC_WORDS
from signal_lab.gui.theme import ScientificPalette, get_monospace_font, get_ui_font


class BitstreamViewer(QWidget):
    """Scientific bitstream inspector with preamble highlighting and click-to-time navigation."""

    time_navigated = Signal(float)  # timestamp in seconds
    sample_navigated = Signal(int)  # sample index in capture buffer

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._bits: np.ndarray = np.zeros(0, dtype=np.uint8)
        self._sample_rate_hz: float = 1.0
        self._samples_per_symbol: int = 4
        self._bits_per_symbol: int = 2  # default QPSK

        self._init_ui()

    def _init_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(10)

        # 1. Top Control Toolbar
        toolbar = QHBoxLayout()
        toolbar.setSpacing(12)

        lbl_mode = QLabel("Display Mode:")
        lbl_mode.setFont(get_ui_font(9, QFont.Weight.Bold))
        lbl_mode.setStyleSheet(f"color: {ScientificPalette.TEXT_MUTED};")
        toolbar.addWidget(lbl_mode)

        self.radio_hex = QRadioButton("Hex + ASCII")
        self.radio_hex.setChecked(True)
        self.radio_hex.toggled.connect(self._render_bitstream)
        toolbar.addWidget(self.radio_hex)

        self.radio_bin = QRadioButton("Binary Matrix")
        self.radio_bin.toggled.connect(self._render_bitstream)
        toolbar.addWidget(self.radio_bin)

        mode_group = QButtonGroup(self)
        mode_group.addButton(self.radio_hex)
        mode_group.addButton(self.radio_bin)

        toolbar.addSpacing(16)

        # Sync Pattern Search
        lbl_search = QLabel("Sync Search:")
        lbl_search.setFont(get_ui_font(9, QFont.Weight.Bold))
        lbl_search.setStyleSheet(f"color: {ScientificPalette.TEXT_MUTED};")
        toolbar.addWidget(lbl_search)

        self.txt_search = QLineEdit()
        self.txt_search.setPlaceholderText("Hex (e.g. 1ACFFC1D) or Bits...")
        self.txt_search.setFixedWidth(160)
        self.txt_search.setFont(get_monospace_font(9))
        self.txt_search.returnPressed.connect(self._on_search)
        toolbar.addWidget(self.txt_search)

        self.btn_search = QPushButton("Find Next")
        self.btn_search.clicked.connect(self._on_search)
        toolbar.addWidget(self.btn_search)

        toolbar.addStretch()

        self.lbl_stats = QLabel("0 bits (0 bytes)")
        self.lbl_stats.setFont(get_monospace_font(9))
        self.lbl_stats.setStyleSheet(f"color: {ScientificPalette.TEXT_SECONDARY};")
        toolbar.addWidget(self.lbl_stats)

        layout.addLayout(toolbar)

        # 2. Central Table Grid
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Offset", "Data Hex", "ASCII", "Annotation / Sync"])
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeMode.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setStyleSheet(
            f"""
            QTableWidget {{
                background-color: {ScientificPalette.BG_BASE};
                color: {ScientificPalette.TEXT_PRIMARY};
                gridline-color: {ScientificPalette.BORDER_SUBTLE};
                font-family: 'JetBrains Mono', monospace;
                font-size: 11px;
                border: 1px solid {ScientificPalette.BORDER_STRONG};
            }}
            QHeaderView::section {{
                background-color: {ScientificPalette.BG_SURFACE};
                color: {ScientificPalette.TEXT_SECONDARY};
                padding: 4px 8px;
                border: 1px solid {ScientificPalette.BORDER_SUBTLE};
                font-weight: bold;
            }}
            QTableWidget::item:selected {{
                background-color: {ScientificPalette.BG_ACTIVE};
                color: {ScientificPalette.ACCENT_CYAN};
            }}
            """
        )
        self.table.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.table)

        # 3. Footer Help Label
        footer = QLabel("💡 Tip: Click any row to center the Waterfall and Waveform on that exact microsecond.")
        footer.setStyleSheet(f"color: {ScientificPalette.TEXT_MUTED}; font-size: 10px;")
        layout.addWidget(footer)

    def set_bitstream(
        self,
        bits: np.ndarray,
        sample_rate_hz: float = 1.0,
        sps: int = 4,
        bits_per_symbol: int = 2,
    ) -> None:
        """Loads demodulated bits into inspector and highlights detected preambles."""
        self._bits = (bits > 0).astype(np.uint8)
        self._sample_rate_hz = sample_rate_hz
        self._samples_per_symbol = sps
        self._bits_per_symbol = max(1, bits_per_symbol)

        num_bytes = len(self._bits) // 8
        self.lbl_stats.setText(f"{len(self._bits):,} bits ({num_bytes:,} bytes)")
        self._render_bitstream()

    def _render_bitstream(self) -> None:
        self.table.setRowCount(0)
        if len(self._bits) == 0:
            return

        is_hex = self.radio_hex.isChecked()
        bytes_per_row = 16 if is_hex else 4
        bits_per_row = bytes_per_row * 8

        num_rows = min(500, (len(self._bits) + bits_per_row - 1) // bits_per_row)
        self.table.setRowCount(num_rows)

        # Pre-detect standard preambles
        preamble_locations = self._find_standard_preambles()

        for r in range(num_rows):
            bit_offset = r * bits_per_row
            row_bits = self._bits[bit_offset : bit_offset + bits_per_row]

            # Offset column
            item_offset = QTableWidgetItem(f"0x{bit_offset // 8:06X}")
            item_offset.setForeground(QColor(ScientificPalette.TEXT_MUTED))
            self.table.setItem(r, 0, item_offset)

            # Data formatting
            if is_hex:
                hex_strs = []
                ascii_chars = []
                for b_idx in range(0, len(row_bits), 8):
                    byte_bits = row_bits[b_idx : b_idx + 8]
                    if len(byte_bits) == 8:
                        val = int("".join(map(str, byte_bits)), 2)
                        hex_strs.append(f"{val:02X}")
                        ascii_chars.append(chr(val) if 32 <= val <= 126 else ".")
                    else:
                        hex_strs.append("..")
                        ascii_chars.append(" ")
                data_text = " ".join(hex_strs)
                ascii_text = "".join(ascii_chars)
            else:
                data_text = "".join(map(str, row_bits))
                ascii_text = ""

            item_data = QTableWidgetItem(data_text)
            item_ascii = QTableWidgetItem(ascii_text)

            # Annotation column
            sync_match = preamble_locations.get(r, "")
            item_annot = QTableWidgetItem(sync_match)
            if sync_match:
                item_data.setForeground(QColor(ScientificPalette.ACCENT_CYAN))
                item_data.setBackground(QColor("#002830"))
                item_annot.setForeground(QColor(ScientificPalette.ACCENT_AMBER))
                item_annot.setFont(get_ui_font(9, QFont.Weight.Bold))

            self.table.setItem(r, 1, item_data)
            self.table.setItem(r, 2, item_ascii)
            self.table.setItem(r, 3, item_annot)

    def _find_standard_preambles(self) -> dict[int, str]:
        """Scans for Barker and CCSDS preambles and maps them to row indices."""
        locations: dict[int, str] = {}
        bytes_per_row = 16 if self.radio_hex.isChecked() else 4
        bits_per_row = bytes_per_row * 8

        # Check Barker 13 (1101110010000 or inverted)
        barker_13 = STANDARD_SYNC_WORDS.get("Barker_13")
        if barker_13 is not None and len(self._bits) >= 13:
            b_pat = np.array(barker_13, dtype=np.uint8)
            for i in range(min(500 * bits_per_row, len(self._bits) - 13)):
                if np.array_equal(self._bits[i : i + 13], b_pat):
                    row_idx = i // bits_per_row
                    locations[row_idx] = "Barker-13 Sync Detected"
                    break

        # Check CCSDS 32-bit (0x1ACFFC1D)
        ccsds_raw = STANDARD_SYNC_WORDS.get("CCSDS_ASM_32")
        if ccsds_raw is not None and len(self._bits) >= 32:
            if len(ccsds_raw) == 32:
                c_pat = np.array(ccsds_raw, dtype=np.uint8)
            else:
                c_pat = np.array(
                    [int(b) for byte in ccsds_raw for b in f"{byte:08b}"], dtype=np.uint8
                )
            for i in range(min(500 * bits_per_row, len(self._bits) - 32)):
                if np.array_equal(self._bits[i : i + 32], c_pat):
                    row_idx = i // bits_per_row
                    locations[row_idx] = "CCSDS ASM (0x1ACFFC1D)"
                    break

        return locations

    def _on_item_clicked(self, item: QTableWidgetItem) -> None:
        row = item.row()
        bytes_per_row = 16 if self.radio_hex.isChecked() else 4
        bit_offset = row * bytes_per_row * 8

        # Calculate corresponding sample index in physical signal
        symbol_index = bit_offset // self._bits_per_symbol
        sample_index = symbol_index * self._samples_per_symbol
        timestamp_s = sample_index / self._sample_rate_hz if self._sample_rate_hz > 0 else 0.0

        self.sample_navigated.emit(sample_index)
        self.time_navigated.emit(timestamp_s)

    def _on_search(self) -> None:
        query = self.txt_search.text().strip().upper()
        if not query:
            return

        # Search across row contents
        for r in range(self.table.rowCount()):
            item = self.table.item(r, 1)
            if item and query in item.text().replace(" ", "").upper():
                self.table.selectRow(r)
                self.table.scrollToItem(item)
                self._on_item_clicked(item)
                return
