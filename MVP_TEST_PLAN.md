# Python Bubble Tea — MVP Test Plan

This document describes the manual and automated test scenarios for validating the
Python port of Bubble Tea at MVP status. It is intended as a guide for human testers
verifying end-to-end behaviour that cannot be fully covered by headless unit tests.

---

## Prerequisites

```bash
git clone <repo-url>
cd bubbletea
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

Verify the automated suite passes first:

```bash
pytest
# Expected: 117 passed
mypy __init__.py tea.py commands.py model.py messages.py keys.py mouse.py renderer.py screen.py exec.py log.py
# Expected: Success: no issues found
```

---

## 1. Automated Test Suite

Run `pytest -v` and confirm all 117 tests pass across:

| Test file | Coverage area |
|-----------|--------------|
| `tests/test_keys.py` | Key name lookup, printable ASCII, control chars, arrow/nav keys, function keys f1–f12, alt combos, multi-byte UTF-8, escape |
| `tests/test_mouse.py` | SGR press/release/motion, wheel events, modifier combinations; X10 press/release; malformed/short buffers |
| `tests/test_commands.py` | `batch()`, `sequence()`, `tick()`, `every()`, `window_size()` |
| `tests/test_renderer.py` | Lifecycle (start/stop/kill/close), flush behaviour, clear, cursor/screen sequences, FPS coalescing, NullRenderer no-ops |
| `tests/test_screen.py` | All 8 command factories produce correct `Msg` subclass and are callable |
| `tests/test_program.py` | Init cmd delivery, final model return, `send()`, `kill()`, `wait()`, filter, NullRenderer swap, `stop_event` cancellation |

**Pass criteria**: `117 passed, 0 failed, 0 errors`

---

## 2. Example Programs — Manual Testing

All examples should be run from the repo root. Terminate with `q` or `ctrl+c` unless
instructed otherwise.

### 2.1 `examples/simple.py` — Countdown timer

```bash
python examples/simple.py
```

**Checklist**:
- [ ] TUI renders cleanly: shows countdown from 5
- [ ] Counter decrements once per second (approx)
- [ ] Program exits automatically when counter reaches 0
- [ ] `q` key quits immediately
- [ ] `ctrl+c` quits without corrupting the terminal
- [ ] `ctrl+z` suspends the process (`bg`/`fg` resumes and TUI repaints)
- [ ] Terminal is left in normal (cooked) mode after exit

### 2.2 `examples/http.py` — Background HTTP request

```bash
python examples/http.py
```

**Checklist**:
- [ ] TUI shows "Fetching…" spinner or status while request is in-flight
- [ ] Result (success or error) is displayed within a few seconds
- [ ] `q` / `ctrl+c` exits cleanly at any point, including while request is pending
- [ ] Terminal restored after exit

### 2.3 `examples/mouse.py` — Mouse events

```bash
python examples/mouse.py
```

**Checklist**:
- [ ] Left-click logs a `MouseMsg` with correct coordinates and `PRESS` action
- [ ] Mouse release logs a `RELEASE` action
- [ ] Moving the mouse logs `MOTION` events (all-motion mode)
- [ ] Right-click and middle-click produce distinct button values
- [ ] Scroll wheel up/down produces `WHEEL_UP` / `WHEEL_DOWN`
- [ ] Holding shift/alt/ctrl while clicking shows modifier flags in the log
- [ ] `q` / `ctrl+c` exits cleanly

### 2.4 `examples/realtime.py` — Real-time updates via `send()`

```bash
python examples/realtime.py
```

**Checklist**:
- [ ] Display updates in real time (new lines appear without key presses)
- [ ] Updates arrive at a consistent rate from the background thread
- [ ] `q` / `ctrl+c` exits cleanly without hanging

### 2.5 `examples/send_msg.py` — Spinner + external `send()`

```bash
python examples/send_msg.py
```

**Checklist**:
- [ ] Spinner animation plays smoothly
- [ ] Background thread messages appear above or alongside the spinner
- [ ] `q` / `ctrl+c` exits cleanly

### 2.6 `examples/views.py` — Multiple views

```bash
python examples/views.py
```

**Checklist**:
- [ ] Initial view (choice list) renders with selectable options
- [ ] Arrow keys or `j`/`k` move the selection highlight
- [ ] `enter` transitions to the next view
- [ ] Progress bar or secondary view renders correctly
- [ ] `q` / `ctrl+c` exits from any view

### 2.7 `examples/exec.py` — External editor handoff

```bash
EDITOR=nano python examples/exec.py
# or
python examples/exec.py   # uses $EDITOR or falls back to vim
```

**Checklist**:
- [ ] Pressing `e` clears the TUI and opens the editor with full terminal access
- [ ] Editor is fully interactive (arrow keys, typing, saving work correctly)
- [ ] After closing the editor, the TUI resumes and repaints correctly
- [ ] `a` toggles alt-screen before/after editor sessions
- [ ] `q` exits cleanly
- [ ] If editor exits non-zero (e.g. `kill` the editor), the TUI handles the error
  gracefully (prints error and exits rather than hanging or crashing)

---

## 3. Signal Handling

Test on a Unix terminal (macOS or Linux).

### 3.1 SIGTERM — graceful shutdown

```bash
python examples/simple.py &
PID=$!
sleep 1
kill $PID          # sends SIGTERM
echo "Exit: $?"
reset              # only needed if terminal is corrupted
```

**Expected**:
- [ ] Program exits within ~1 second
- [ ] Terminal is restored to cooked mode (no need for `reset`)
- [ ] Exit code is 0 or non-zero (acceptable); terminal must be clean

### 3.2 SIGTSTP / SIGCONT — suspend and resume

```bash
python examples/simple.py
# Press ctrl+z to suspend
fg   # or: kill -CONT $PID
```

**Expected**:
- [ ] `ctrl+z` suspends cleanly (terminal returns to shell prompt)
- [ ] `fg` resumes and TUI repaints without corruption
- [ ] Countdown continues from where it left off

### 3.3 SIGINT — interrupt vs quit

The `simple.py` example catches `ErrInterrupted` and exits silently.

```bash
python examples/simple.py
# Press ctrl+c
```

**Expected**:
- [ ] Program exits immediately
- [ ] Terminal is restored (no raw-mode leftovers)
- [ ] No Python traceback printed

---

## 4. Alt-Screen Mode

```bash
python examples/exec.py
# Press 'a' to toggle alt-screen
# Press 'a' again to return to normal screen
# Press 'q' to quit
```

**Checklist**:
- [ ] Entering alt-screen hides scrollback history and clears the display
- [ ] Exiting alt-screen restores the previous scrollback content
- [ ] After `q`, normal terminal history is visible

---

## 5. Debug Logging

```bash
BUBBLETEA_LOG=debug.log python examples/simple.py &
tail -f debug.log
```

**Checklist**:
- [ ] `debug.log` is created and written to during execution
- [ ] Log entries appear in real time (within ~1 second)
- [ ] TUI display is not corrupted by logging (nothing written to stdout/stderr)

---

## 6. Context / Stop-Event Cancellation

This is exercised by the automated tests (`test_program.py::test_stop_event_exits`), but
can also be validated manually by inspecting the test or writing a small script:

```python
import threading, bubbletea as tea, io
from tests.conftest import make_program

stop = threading.Event()
_, p = make_program(MyModel(), stop_event=stop)
# start p in a thread, set stop after 0.5s, assert p.run() returns
```

**Pass criteria**: `p.run()` returns within ~1 second of `stop.set()` being called.

---

## 7. Type Safety

```bash
mypy __init__.py tea.py commands.py model.py messages.py keys.py mouse.py renderer.py screen.py exec.py log.py
```

**Pass criteria**: `Success: no issues found in 11 source files`

---

## 8. Code Quality

```bash
black --check .
isort --check .
flake8
```

**Pass criteria**: No output (exit code 0) from all three commands.

---

## 9. Packaging Smoke Test

```bash
pip install build
python -m build --wheel --outdir /tmp/bt-dist .
pip install /tmp/bt-dist/bubbletea-*.whl --force-reinstall
python -c "import bubbletea as tea; print(tea.__version__)"
```

**Expected output**: `0.1.0`

**Checklist**:
- [ ] Wheel builds without errors
- [ ] Package installs cleanly
- [ ] `import bubbletea` succeeds and `__version__` is correct
- [ ] `py.typed` marker is present in the installed package (enables type checking for
  downstream users):
  ```bash
  python -c "import importlib.resources as r, bubbletea; print(list(r.files(bubbletea).iterdir()))" | grep py.typed
  ```

---

## Pass / Fail Criteria Summary

| Area | Automated | Manual |
|------|-----------|--------|
| Unit tests (117) | `pytest` — 0 failures | — |
| Type safety | `mypy` — 0 errors | — |
| Code style | `black`/`isort`/`flake8` — 0 errors | — |
| Simple example | — | All checklist items |
| HTTP example | — | All checklist items |
| Mouse example | — | All checklist items |
| Realtime example | — | All checklist items |
| Send-msg example | — | All checklist items |
| Views example | — | All checklist items |
| Exec example | — | All checklist items |
| Signal handling | — | SIGTERM, SIGTSTP, SIGINT |
| Alt-screen | — | Toggle in/out cleanly |
| Debug logging | — | File written, TUI clean |
| Packaging | Wheel build | Import + version + py.typed |

MVP is considered **PASSED** when all automated checks are green and all manual
checklist items in sections 2–9 are ticked.
