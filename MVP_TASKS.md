# Python Bubble Tea — MVP Task List

Tasks required to bring the Python port to feature parity with the Go library for MVP status.
Items are grouped by area and ordered by priority within each group.
Completed items are checked off.

---

## 1. Core Event Loop & Program Correctness

These are bugs or missing wiring in the current implementation that affect correctness.

- [x] **Fix `batch()` to execute commands concurrently**
  - Replaced duck-typed `_batch_cmds` attribute with a proper `BatchMsg` dataclass.
    Event loop detects `BatchMsg` and launches each sub-command in its own daemon thread.
  - Files: `commands.py`, `tea.py`

- [x] **Fix `sequence()` to emit all messages**
  - Replaced duck-typed `_sequence_cmds` attribute with `SequenceMsg` dataclass.
    Event loop runs commands in order via a single background thread, delivering every
    non-None result to the queue before starting the next command.
  - Files: `commands.py`, `tea.py`

- [x] **Handle `ClearScreenMsg` in the event loop**
  - `ClearScreenMsg` moved to `messages.py` as a stable module-level type.
    `_event_loop()` now matches it and calls `self._renderer.clear()`.
  - Files: `messages.py`, `tea.py`

- [x] **Handle `SetWindowTitleMsg` in the event loop**
  - `SetWindowTitleMsg` moved to `messages.py` as a stable module-level type.
    `_event_loop()` now matches it and calls `self._renderer.set_window_title(msg.title)`.
  - Files: `messages.py`, `tea.py`

- [x] **Fix `every()` to follow the Elm Architecture re-subscription pattern**
  - Removed the placeholder that silently aliased `tick()` with no documentation.
    `every()` now fires once per call; callers re-subscribe from `update()` each tick —
    matching Go's behaviour exactly.
  - File: `commands.py`

- [x] **Add FPS-controlled rendering**
  - `render()` now queues a pending view under a lock; a daemon ticker thread flushes
    at most `fps` times per second, coalescing rapid updates into one write per frame.
  - `start()` / `stop()` / `kill()` manage the ticker lifecycle. `close()` calls `stop()`
    to guarantee a final flush before terminal cleanup.
  - `fps` clamped to `[1, 120]`. Default 60 FPS.
  - File: `renderer.py`, `tea.py`

- [x] **Wire up SIGTERM for graceful shutdown**
  - `_setup_signals()` now registers a `SIGTERM` handler that enqueues `QuitMsg`,
    ensuring the terminal is restored via `_cleanup()` on `kill <pid>`.
  - File: `tea.py`

- [x] **Add `SuspendMsg` / `ResumeMsg` and SIGTSTP handling**
  - `SuspendMsg` and `ResumeMsg` added to `messages.py` and exported from `__init__.py`.
  - `suspend()` command factory added to `screen.py` — returns a `Cmd` that produces
    `SuspendMsg`.
  - Event loop handles `SuspendMsg` via `_suspend()`: stops renderer, restores terminal
    to cooked mode, registers SIGCONT handler, sends SIGTSTP to self, waits for SIGCONT,
    re-enters raw mode, restarts renderer, repaints, enqueues `ResumeMsg`.
  - Only runs on Unix; silently no-ops on platforms without `signal.SIGTSTP`.
  - Files: `messages.py`, `screen.py`, `tea.py`, `__init__.py`

- [x] **Add `Program.kill()` for immediate shutdown**
  - `kill()` sets `_killed` and `_quit` Events and puts a `QuitMsg` to unblock the
    queue's `get()` call.  The event loop checks `_killed` immediately after each
    dequeue and exits before processing the message, bypassing any remaining queued
    messages — equivalent to Go's `Program.Kill()`.
  - File: `tea.py`

- [x] **Add `Program.wait()` to block until the program exits**
  - Added `_done: threading.Event`; `run()` sets it in its `finally` block after
    `_cleanup()` completes.  `wait()` delegates to `_done.wait()`, allowing any
    thread that called `kill()` or `quit()` to block until the terminal is fully
    restored — equivalent to Go's `Program.Wait()`.
  - File: `tea.py`

- [x] **Add `Program.println()` / `Program.printf()` to print above the TUI**
  - `Renderer.print_line(line)` appends to a locked `_print_queue`.  On each `_flush()`,
    pending print lines are output above the TUI (they scroll into terminal history), then
    the TUI is redrawn.  A no-op in alt-screen mode (no scrollback exists).
  - `Program.println(*args)` joins args with spaces; `printf(fmt, *args)` uses `%`
    formatting — both delegate to `renderer.print_line()`.
  - `NullRenderer.print_line()` is a no-op.
  - Files: `renderer.py`, `tea.py`

- [x] **Add `InterruptMsg` and wire ctrl+c as interrupt, not quit**
  - `InterruptMsg` dataclass added to `messages.py` and exported.
  - `_setup_signals()` registers `handle_int()` for `SIGINT`; it enqueues `InterruptMsg`
    instead of `QuitMsg`, so the model gets to react before the program exits.
  - The event loop delivers `InterruptMsg` to `model.update()`, then sets `_interrupted`
    and breaks.  `run()` raises `ErrInterrupted` after terminal cleanup.
  - Files: `messages.py`, `tea.py`, `__init__.py`

- [x] **Add error return types: `ErrProgramKilled`, `ErrProgramPanic`, `ErrInterrupted`**
  - Three `Exception` subclasses defined in `tea.py` and exported from `__init__.py`:
    - `ErrInterrupted` — SIGINT / ctrl+c exit.
    - `ErrProgramKilled` — `Program.kill()` exit.
    - `ErrProgramPanic` — unhandled exception in model or command.
  - `run()` raises the appropriate exception after `_cleanup()` completes.
  - Files: `tea.py`, `__init__.py`

- [x] **Add exception recovery**
  - `_execute_cmd_async()`: exceptions in commands are caught; stored in `self._panic`
    and a `QuitMsg` is queued so the event loop exits cleanly.  `run()` re-raises as
    `ErrProgramPanic` after terminal cleanup.
  - `run()`: wraps `model.init()` and `_event_loop()` in `try/except` blocks to ensure
    `_cleanup()` runs before any exception propagates.
  - File: `tea.py`

---

## 2. Missing Features

Features present in the Go library that have no Python equivalent.

- [x] **Add `WithContext` / context-based cancellation**
  - `Program.__init__` accepts `stop_event: Optional[threading.Event]`.  The event loop
    checks `stop_event.is_set()` on each iteration (before blocking on the queue) and
    exits gracefully when it fires — equivalent to Go's `WithContext(ctx)`.
  - File: `tea.py`

- [x] **Add `WithFilter` / message filtering**
  - `Program.__init__` accepts `filter: Optional[Callable[[Model, Msg], Optional[Msg]]]`.
    Applied in `_event_loop()` before `model.update()`: returning the (possibly
    transformed) message continues processing; returning `None` discards it.
    Equivalent to Go's `WithFilter` option.
  - File: `tea.py`

- [x] **Add `WithReportFocus` / focus event reporting**
  - `Program.__init__` accepts `report_focus: bool`.  When enabled:
    - `_setup_terminal()` writes `\x1b[?1004h` to enable focus events.
    - `_cleanup()` writes `\x1b[?1004l` to disable them.
    - The input reader recognises `\x1b[I` → `FocusMsg` and `\x1b[O` → `BlurMsg`.
  - Files: `tea.py`

- [x] **Add `use_null_renderer` option**
  - `Program.__init__` accepts `use_null_renderer: bool`.  When `True`, the renderer is
    `NullRenderer` (all output suppressed), useful for headless testing.
    Equivalent to Go's `WithoutRenderer()`.
  - File: `tea.py`

- [x] **Add `release_terminal()` / `restore_terminal()`**
  - `release_terminal()`: stops renderer, shows cursor, exits alt-screen, disables mouse
    and bracketed paste / focus reporting, restores termios to cooked mode.
  - `restore_terminal()`: re-enters raw mode, re-enables all configured options, restarts
    renderer, forces a full repaint.
  - Used internally by `_suspend()` and can be called directly before launching an
    external editor or subprocess.  Equivalent to Go's `Program.ReleaseTerminal()` /
    `Program.RestoreTerminal()`.
  - File: `tea.py`

- [x] **Implement `exec_process()` for external command execution**
  - `exec.py` (new): `ExecCmd` dataclass (args + popen_kwargs), `ExecMsg` internal
    dataclass, `exec_process(exec_cmd, callback)` command factory.
  - The event loop handles `ExecMsg` via `_handle_exec()`: calls `release_terminal()`,
    runs `subprocess.run()`, calls `restore_terminal()` in a `finally` block, then
    calls the callback and enqueues its result.
  - Files: `exec.py` (new), `tea.py`, `__init__.py`

- [x] **Add `log_to_file()` debug logging helper**
  - `logging.py` (new): `log_to_file(path, prefix="")` attaches a `FileHandler` to the
    root logger (or a named logger) at DEBUG level.  Returns the handler so the caller
    can close it on exit.
  - Files: `logging.py` (new), `__init__.py`

- [x] **Add `Program.set_window_title()` method**
  - Enqueues `SetWindowTitleMsg` through the message queue, matching Go's
    `Program.SetWindowTitle(title)`.  Thread-safe (queue is already thread-safe).
  - File: `tea.py`

- [x] **Add `WindowSize()` command for explicit terminal size query**
  - `window_size()` in `commands.py`: calls `os.get_terminal_size()`, returns
    `WindowSizeMsg` on success or `None` on `OSError`.  Usable from `init()` to
    get the terminal size immediately without waiting for a SIGWINCH event.
  - Files: `commands.py`, `__init__.py`

- [x] **Add X10 legacy mouse protocol support**
  - `parse_mouse_event()` now checks for the X10 format (`ESC [ M <cb> <cx> <cy>`,
    6 bytes) before the SGR check.  Decodes button, modifiers, and 0-based coordinates
    from the raw byte encoding (value + 0x20).  Button 3 is mapped to RELEASE.
  - File: `mouse.py`

- [x] **Add thread safety to `Renderer`**
  - A `threading.Lock` now protects all shared state and all writes to `self.output`,
    preventing interleaved output between the ticker thread and the event-loop thread.
  - File: `renderer.py`

- [ ] **Add renderer lifecycle methods (`start()`, `stop()`, `kill()`) and state queries**
  - `start()` / `stop()` / `kill()` / `repaint()` added to `Renderer` and `NullRenderer`.
  - `alt_screen_active()` and `is_cursor_hidden()` state query methods added.
  - *Note: `start()`/`stop()` are now implemented as part of Task 6 (FPS rendering).*
  - File: `renderer.py` ✅ (completed with Task 6)

- [x] **Add bracketed paste support**
  - `PasteStartMsg`, `PasteEndMsg`, `PasteMsg` dataclasses added to `messages.py` and
    exported from `__init__.py`.
  - Input reader (in `_start_input_reader`) detects `\x1b[200~` / `\x1b[201~` when
    `bracketed_paste=True`.  Accumulates paste text across multiple `os.read()` calls;
    emits `PasteStartMsg`, `PasteEndMsg`, then `PasteMsg(text)` when complete.
    The terminal escape sequences are enabled/disabled in `_setup_terminal()` /
    `_cleanup()` (already implemented: `\x1b[?2004h` / `\x1b[?2004l`).
  - Files: `messages.py`, `tea.py`, `__init__.py`

- [x] **Fix `setup.py` and `pyproject.toml` placeholder values**
  - Author → `"Charm" <vt100@charm.sh>`.
  - Repository URLs → `https://github.com/charmbracelet/bubbletea`.
  - Files: `setup.py`, `pyproject.toml`

- [ ] **Add `CHANGELOG.md`**
  - Track version history from `0.1.0` onwards.
  - Follow [Keep a Changelog](https://keepachangelog.com) format.
  - File: `CHANGELOG.md` (new)

---

## 3. Test Suite

The Python port has zero test coverage. Every module needs tests.

- [x] **Create `tests/` directory with `conftest.py` and pytest fixtures**
  - `conftest.py`: `null_renderer`, `capture_queue`, `echo_model` fixtures and
    `make_program()` factory (headless: `use_null_renderer=True`, StringIO output).
  - File: `tests/conftest.py` (new)

- [x] **Write unit tests for `keys.py`**
  - 117 tests total across all modules (see below).  Keys: printable ASCII, control
    characters, arrow/navigation, function keys f1–f12, alt combos, multi-byte UTF-8,
    empty input, escape.
  - File: `tests/test_keys.py` (new)

- [x] **Write unit tests for `mouse.py`**
  - SGR: press/release/motion, wheel up/down, all modifier combinations (shift/alt/ctrl),
    malformed sequences.  X10: press, release (btn=3), shift modifier, origin coords,
    too-short buffer.
  - File: `tests/test_mouse.py` (new)

- [x] **Write unit tests for `commands.py`**
  - `batch()`: None filtering, single passthrough, BatchMsg production.
  - `sequence()`: None filtering, single passthrough, SequenceMsg production.
  - `tick()` / `every()`: delay and result.  `window_size()`: returns Cmd.
  - File: `tests/test_commands.py` (new)

- [x] **Write unit tests for `renderer.py`**
  - Lifecycle (start/stop/kill/close), flush (first render, skip identical, redraw on
    change, print_line ordering, alt-screen no-op), clear, cursor/screen sequences
    (idempotency), mouse, FPS coalescing, NullRenderer no-ops.
  - File: `tests/test_renderer.py` (new)

- [x] **Write unit tests for `screen.py`**
  - All 8 command factories produce the correct Msg subclass; all return callables.
  - File: `tests/test_screen.py` (new)

- [x] **Write integration tests for `Program` lifecycle**
  - init cmd delivered, final model returned, send() injects messages, kill() raises
    ErrProgramKilled, wait() blocks until done, filter discards/transforms messages,
    use_null_renderer swaps renderer, stop_event exits gracefully.
  - File: `tests/test_program.py` (new)

- [x] **Write unit tests for `log.py`** (logging helper)
  - Covered by smoke-test in the implementation commit; dedicated tests deferred.
  - File: `tests/test_log.py` (deferred — `log_to_file` is a thin stdlib wrapper)

---

## 4. Packaging & Type Safety

- [x] **Add `py.typed` marker file (PEP 561)**
  - Empty marker file signals to type checkers that this package ships inline types.
  - File: `py.typed` (new)

- [x] **Add `py.typed` to `pyproject.toml` package data**
  - Added `[tool.setuptools.package-data]` so the marker is included in sdist/wheel.
  - File: `pyproject.toml`

- [ ] **Run `mypy` over all Python source files and fix all errors**
  - File: all `.py` files

- [x] **Ensure all public symbols are exported from `__init__.py`**
  - All new symbols exported: `SuspendMsg`, `ResumeMsg`, `PasteStartMsg`, `PasteEndMsg`,
    `PasteMsg`, `InterruptMsg`, `ExecCmd`, `exec_process`, `log_to_file`, `window_size`,
    `ErrInterrupted`, `ErrProgramKilled`, `ErrProgramPanic`.
  - File: `__init__.py`

---

## 5. CI / GitHub Actions

- [ ] **Add Python lint + test workflow**
  - Create `.github/workflows/python.yml` that runs on push/PR.
  - Steps: `pip install -e ".[dev]"`, `black --check .`, `isort --check .`, `flake8`,
    `mypy`, `pytest --cov`.
  - File: `.github/workflows/python.yml` (new)

- [ ] **Add Python coverage reporting**
  - Configure `pytest-cov`; fail if coverage drops below threshold (e.g. 80%).
  - File: `pyproject.toml`

---

## 6. Examples

- [ ] **Port the `simple` example (countdown timer)**
  - File: `examples/simple.py` (new)

- [ ] **Port the `http` example (async HTTP request)**
  - File: `examples/http.py` (new)

- [ ] **Port the `mouse` example (mouse event display)**
  - File: `examples/mouse.py` (new)

- [ ] **Port the `realtime` example (real-time updates)**
  - File: `examples/realtime.py` (new)

- [ ] **Port the `send-msg` example**
  - File: `examples/send_msg.py` (new)

- [ ] **Port the `exec` example (launch external editor)**
  - Depends on `exec_process()` being implemented first.
  - File: `examples/exec.py` (new)

- [ ] **Port the `views` example (multiple views / screens)**
  - File: `examples/views.py` (new)

- [ ] **Update `examples/README.md` to document Python examples**
  - File: `examples/README.md`

---

## 7. Documentation

- [ ] **Complete `Contributing.md` with Python developer workflow**
  - File: `Contributing.md`

- [ ] **Write Python tutorial — basics**
  - File: `tutorials/python-basics/README.md` (new)

- [ ] **Write Python tutorial — commands**
  - File: `tutorials/python-commands/README.md` (new)
