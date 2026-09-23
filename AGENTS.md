---
trigger: always_on
description: Autonomous project build permissions and operational rules for Signal Lab
---

# Autonomous Execution & Permissions Rule

Refer to [PERMISSIONS.md](file:///home/alekh/projects/ps2/PERMISSIONS.md) for full operational boundaries.

## Active Granted Permissions
1. **Environment & Dependencies**: Create and manage local virtual environment (`.venv`) using `uv` with Python 3.12+ and install required scientific dependencies (`PySide6`, `pyqtgraph`, `numpy`, `scipy`, `pytest`, `pytest-qt`, `ruff`, `pydantic`, `torch`, `pybind11`).
2. **Filesystem Operations**: Create, edit, refactor, and maintain all source files, schemas, and test fixtures within `/home/alekh/projects/ps2`.
3. **Compilation & Testing**: Run `cmake`, compile C++ kernels, execute `pytest` (including offscreen Qt headless mode `QT_QPA_PLATFORM=offscreen`), and run linters (`ruff`).
4. **Autonomous Flow**: Execute all project phases without asking repetitive step-by-step permissions, operating strictly within workspace safety boundaries.
