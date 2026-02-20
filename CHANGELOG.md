# Changelog

All notable changes to the **Python port** of Bubble Tea are documented here.
Changes to the original Go library are not tracked in this file.

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
The Python port uses [Semantic Versioning](https://semver.org/).

---

## [Unreleased]

### Added (Python port)

- **Core event loop**
  - `batch()` executes commands concurrently in daemon threads; all results delivered independently.
  - `sequence()` executes commands in order; each result delivered before the next starts.
  - `ClearScreenMsg` / `SetWindowTitleMsg` handled by the event loop.
  - `every()` follows the Elm Architecture re-subscription pattern (fires once per call).
  - FPS-capped, thread-safe `Renderer` with `start()` / `stop()` / `kill()` / `repaint()`.
  - `SIGTERM` handler enqueues `QuitMsg` for graceful terminal cleanup on `kill <pid>`.
  - `SuspendMsg` / `ResumeMsg`: ctrl-z support via SIGTSTP / SIGCONT cycle.
  - `Program.kill()` — immediate shutdown bypassing the message queue.
  - `Program.wait()` — block until `run()` completes and terminal is restored.
  - `Program.println()` / `Program.printf()` — print lines above the TUI into scrollback.
  - `InterruptMsg` — SIGINT / ctrl-c delivers the message to `update()` before exiting.
  - `ErrInterrupted`, `ErrProgramKilled`, `ErrProgramPanic` — typed exit exceptions from `run()`.
  - Exception recovery: command panics stored in `_panic`; `run()` re-raises as `ErrProgramPanic`.
  - `stop_event` constructor parameter — threading.Event-based context cancellation.
  - `filter` constructor parameter — intercept/transform/discard every message before `update()`.
  - `report_focus` constructor parameter — emit `FocusMsg` / `BlurMsg` on terminal focus events.
  - `use_null_renderer` constructor parameter — headless rendering for tests.
  - `Program.release_terminal()` / `Program.restore_terminal()` — hand back and reclaim the TTY.
  - `Program.set_window_title()` — set title from outside the model.
  - `exec_process()` / `ExecCmd` — run an external process with full terminal access.
  - `log_to_file()` — redirect logging to a file (stdout is occupied by the TUI).
  - `window_size()` command — query current terminal dimensions from `init()`.
  - X10 legacy mouse protocol parsed alongside SGR in `parse_mouse_event()`.
  - Bracketed paste: `PasteStartMsg` / `PasteEndMsg` / `PasteMsg` emitted when `bracketed_paste=True`.

- **Packaging**
  - `py.typed` marker (PEP 561) — package ships inline type information.
  - `pyproject.toml` package-data includes `py.typed`.
  - Author / URL metadata updated from placeholders to `charm.sh` values.

- **Tests**
  - 117 tests across `keys`, `mouse`, `commands`, `renderer`, `screen`, and `Program` lifecycle.

- **CI**
  - `.github/workflows/python.yml`: lint + test matrix across Python 3.10 / 3.11 / 3.12,
    plus a coverage gate job (`--cov-fail-under=60`).

- **Examples** (Python)
  - `examples/simple.py` — countdown timer with SIGTSTP / ctrl-z support.
  - `examples/realtime.py` — real-time updates from a background thread via `send()`.
  - `examples/send_msg.py` — spinning food-eater driven by `send()` from a thread.
  - `examples/views.py` — multi-view app with choice list and animated progress bar.
  - `examples/mouse.py` — live mouse event log with all-motion tracking.
  - `examples/http.py` — async HTTP fetch using a background Cmd.

---

## [0.1.0] — Initial Python port

### Added

- `Model` abstract base class (`init`, `update`, `view`).
- `Program` with `run()`, `quit()`, `send()`.
- `KeyMsg`, `MouseMsg`, `WindowSizeMsg`, `FocusMsg`, `BlurMsg`, `QuitMsg`.
- `quit_cmd`, `batch()`, `sequence()`, `tick()`, `every()`.
- `Renderer` (FPS-capped) and `NullRenderer`.
- Screen control commands: `enter_alt_screen`, `exit_alt_screen`, `hide_cursor`,
  `show_cursor`, `enable_mouse_cell_motion`, `enable_mouse_all_motion`, `disable_mouse`.
- SGR mouse protocol parsing.
- `parse_key()` with ANSI escape sequence table.
- `SIGWINCH` handler for window resize.
