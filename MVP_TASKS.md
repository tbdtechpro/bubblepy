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

- [ ] **Implement `exec_process()` for external command execution**
  - Go's `ExecProcess(cmd, callback)` suspends the TUI, runs an interactive subprocess
    with full terminal access, then resumes and delivers the error via a message.
  - Implement using `subprocess.Popen` after `release_terminal()`, with
    `restore_terminal()` in a `finally` block.
  - Add `ExecCmd` abstract base class, `exec_process()` command factory.
  - Files: `exec.py` (new), `tea.py`, `__init__.py`

- [ ] **Add `log_to_file()` debug logging helper**
  - Since the TUI occupies stdout, users cannot use `print()` for debugging.
  - Implement `log_to_file(path: str, prefix: str = "") -> logging.FileHandler` that
    configures Python's `logging` module to write to the given file.
  - Files: `logging.py` (new), `__init__.py`

- [ ] **Add `Program.set_window_title()` method**
  - Add a public method that sends `SetWindowTitleMsg` through the message queue,
    matching Go's `Program.SetWindowTitle(title)`.
  - File: `tea.py`

- [ ] **Add `WindowSize()` command for explicit terminal size query**
  - Go provides a `WindowSize()` command that returns a `WindowSizeMsg` with the current
    dimensions, usable from `init()` without waiting for a resize event.
  - Implement using `os.get_terminal_size()` wrapped in a `Cmd`.
  - Files: `commands.py`, `__init__.py`

- [ ] **Add X10 legacy mouse protocol support**
  - `mouse.py` only parses SGR extended mouse events. Terminals that don't support SGR
    fall back to the X10 protocol (byte-encoded, max coordinate 223).
  - Add an X10 parser alongside the existing SGR parser in `parse_mouse_event()`.
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

- [ ] **Add bracketed paste support**
  - Go supports `WithoutBracketedPaste()` (it's on by default) and emits `PasteMsg` /
    `PasteStartMsg` / `PasteEndMsg`.
  - Add `PasteMsg`, `PasteStartMsg`, `PasteEndMsg` dataclasses to `messages.py`.
  - Parse bracketed paste sequences (`\x1b[200~`...`\x1b[201~`) in the input reader
    when `bracketed_paste=True`.
  - Export from `__init__.py`.
  - Files: `messages.py`, `tea.py`, `__init__.py`

- [ ] **Fix `setup.py` and `pyproject.toml` placeholder values**
  - Author name, email, and repository URLs still contain `"Your Name"`,
    `"your.email@example.com"`, and `"your-repo"`.
  - Files: `setup.py`, `pyproject.toml`

- [ ] **Add `CHANGELOG.md`**
  - Track version history from `0.1.0` onwards.
  - Follow [Keep a Changelog](https://keepachangelog.com) format.
  - File: `CHANGELOG.md` (new)

---

## 3. Test Suite

The Python port has zero test coverage. Every module needs tests.

- [ ] **Create `tests/` directory with `conftest.py` and pytest fixtures**
  - Set up shared fixtures: `null_renderer`, `test_program(model)` factory, `capture_queue`.
  - File: `tests/conftest.py` (new)

- [ ] **Write unit tests for `keys.py`**
  - Test `parse_key()` for: printable ASCII, control characters, arrow/navigation keys,
    function keys f1–f12, alt+key sequences, multi-byte UTF-8, unknown sequences.
  - File: `tests/test_keys.py` (new)

- [ ] **Write unit tests for `mouse.py`**
  - Test `parse_mouse_event()` for: SGR press/release/motion, wheel events, all modifier
    combinations, X10 fallback, malformed sequences.
  - File: `tests/test_mouse.py` (new)

- [ ] **Write unit tests for `commands.py`**
  - Test `batch()`: None filtering, single-cmd passthrough, concurrent execution (verify
    parallelism via timing), all results delivered.
  - Test `sequence()`: order preserved, all messages delivered.
  - Test `tick()`, `every()`.
  - File: `tests/test_commands.py` (new)

- [ ] **Write unit tests for `renderer.py`**
  - Test render/skip-on-identical/clear-and-rewrite cycle.
  - Test FPS coalescing: many rapid renders produce one terminal write per tick.
  - Test alt screen, cursor, mouse sequences.
  - Test `NullRenderer` is a no-op.
  - File: `tests/test_renderer.py` (new)

- [ ] **Write unit tests for `screen.py`**
  - Test each command factory returns a `Cmd` producing the correct message type.
  - File: `tests/test_screen.py` (new)

- [ ] **Write integration tests for `Program` lifecycle**
  - Test `init()` command is executed and its message reaches `update()`.
  - Test `quit_cmd` causes `run()` to return.
  - Test `Program.send()` injects a message.
  - Test `Program.kill()` exits immediately.
  - Test `WithFilter` intercepts messages.
  - File: `tests/test_program.py` (new)

- [ ] **Write unit tests for `logging.py`** (once implemented)
  - File: `tests/test_logging.py` (new)

---

## 4. Packaging & Type Safety

- [ ] **Add `py.typed` marker file (PEP 561)**
  - File: `py.typed` (new)

- [ ] **Add `py.typed` to `pyproject.toml` package data**
  - File: `pyproject.toml`

- [ ] **Run `mypy` over all Python source files and fix all errors**
  - File: all `.py` files

- [ ] **Ensure all public symbols are exported from `__init__.py`**
  - Audit and add any missing exports: `SuspendMsg`, `ResumeMsg`, `PasteMsg`,
    `PasteStartMsg`, `PasteEndMsg`, `ExecCmd`, `exec_process`, `log_to_file`.
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
