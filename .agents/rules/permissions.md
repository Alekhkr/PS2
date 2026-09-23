---
trigger: always_on
description: Autonomous build permissions and workspace boundaries for Signal Lab
---

# Pre-Approved Build Permissions

Full details documented in [PERMISSIONS.md](file:///home/alekh/projects/ps2/PERMISSIONS.md).

- **Scope**: Local workspace `/home/alekh/projects/ps2/` and artifact directories only.
- **Python**: Use `uv` to manage `.venv` with Python 3.12+ and project dependencies.
- **Commands**: Allowed to execute `uv`, `python`, `pytest`, `cmake`, `make`, `ninja`, `ctest`, `ruff`, and GUI test processes autonomously.
- **Continuity**: Build sequentially through project phases without interrupting for routine shell/file permissions.
