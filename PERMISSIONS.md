# Project Permissions & Autonomous Execution Authorization

**Project:** Automated IQ/WAV Signal Analysis Platform ("Signal Lab")  
**Workspace Root:** `/home/alekh/projects/ps2`  
**Target Specification:** [`Signal_Analyzer_Architecture_Gemini_3_8_Flash.md`](file:///home/alekh/projects/ps2/Signal_Analyzer_Architecture_Gemini_3_8_Flash.md)

---

## 1. Scope of Authorization

This document establishes the pre-approved operational boundaries and permissions granted to the AI coding agent to autonomously plan, implement, build, test, and verify the Signal Lab project without requiring repeated manual permission prompts.

### 1.1 Permitted Operational Categories

| Category | Permitted Actions & Tools | Boundary / Safeguards |
|---|---|---|
| **Virtual Environment & Dependencies** | - Run `uv venv` to create/manage Python 3.12+ environments<br>- Install approved scientific, UI, and test packages (`PySide6`, `pyqtgraph`, `numpy`, `scipy`, `pytest`, `pytest-qt`, `ruff`, `pydantic`, `torch`, `pybind11`) | Installed strictly inside local `.venv` within `/home/alekh/projects/ps2`. No global/system package installs. |
| **Filesystem & Codebase Generation** | - Create, edit, and organize project source trees (`signal_lab/`, `tests/`, `cpp/`, `scripts/`, `docs/`)<br>- Generate SQLite database schemas and local session directories<br>- Generate synthetic IQ/WAV fixtures for testing | Strictly confined to `/home/alekh/projects/ps2/` and artifact directory. Original document `Signal_Analyzer_Architecture_Gemini_3_8_Flash.md` is strictly immutable. |
| **Native Compilation & Build** | - Run `cmake`, `make`, `ninja`, `ctest`<br>- Compile C++17/20 native kernels and pybind11 modules for DSP acceleration | Output to `build/` directory within workspace only. |
| **Testing & Verification** | - Run `pytest` and test runners<br>- Run headless UI verification using `QT_QPA_PLATFORM=offscreen`<br>- Run code formatting and linter tools (`ruff check`, `ruff format`) | All test scripts run in user-space without elevated privileges. |
| **Runtime & Display Validation** | - Launch PySide6 GUI processes briefly on active display (`DISPLAY=:1`, `WAYLAND_DISPLAY=wayland-1`) for visual validation<br>- Execute multiprocessing DSP worker jobs | No persistent daemon processes left unmanaged; processes terminated cleanly. |
| **Cache & Cleanup** | - Clean temporary build artifacts (`build/`, `__pycache__/`, `.pytest_cache/`, `.ruff_cache/`) | No recursive deletions outside temporary cache directories. |

---

## 2. Strict Safety Constraints & Prohibitions

1. **No System Privilege Escalation:** Never run `sudo`, `su`, or modify system files outside `/home/alekh/projects/ps2`.
2. **Immutable Input Artifacts:** Original raw captures and the core architecture document (`Signal_Analyzer_Architecture_Gemini_3_8_Flash.md`) shall never be overwritten or deleted.
3. **Offline Integrity:** Core DSP, parameter estimation, demodulation, and FEC decoding must execute entirely offline without remote API dependencies.
4. **Non-Blocking UI Rule:** Heavy computation and DSP loops must never run on the Qt UI thread.

---

## 3. Autonomous Execution Protocol

Upon one-time user confirmation:
- The agent will execute implementation phases sequentially (Phase 1 Foundation through Phase 8 Hardening).
- At each phase, the agent will write modules, implement corresponding unit/integration tests, run verification, and record results without pausing for redundant permissions.
- The agent will only pause if an unrecoverable failure occurs or an explicit architectural trade-off requires user judgment.
