"""Signal Lab — Automated IQ/WAV Signal Analysis Platform.

Main CLI launcher:
    python main.py
"""

import sys

from signal_lab.app import main

if __name__ == "__main__":
    sys.exit(main())
