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

- [ ] **Add `Program.println()` / `Program.printf()` to print above the TUI**
  - Go's `Program.Println()` / `Program.Printf()` inject a `printLineMessage` that the
    renderer outputs above the managed TUI area, persisting across re-renders.
  - Add equivalents that enqueue a print message handled before the next frame.
  - Files: `tea.py`, `renderer.py`

- [ ] **Add `InterruptMsg` and wire ctrl+c as interrupt, not quit**
  - Go distinguishes `InterruptMsg` (SIGINT / ctrl+c) from `QuitMsg`.
  - Add `InterruptMsg` dataclass to `messages.py`; handle SIGINT in `_setup_signals()`
    by sending `InterruptMsg`; handle `InterruptMsg` in `_event_loop()` to break and set
    an interrupted flag on `run()`'s return.
  - Export from `__init__.py`.
  - Files: `messages.py`, `tea.py`, `__init__.py`

- [ ] **Add error return types: `ErrProgramKilled`, `ErrProgramPanic`, `ErrInterrupted`**
  - Go's `Program.Run()` returns typed sentinel errors so callers can distinguish graceful
    quit from kill, interrupt, or panic.
  - Define Python equivalents as exception subclasses; raise appropriately from `run()`.
  - File: `tea.py`

- [ ] **Add exception recovery**
  - Wrap `_event_loop()` and `_execute_cmd_async()` in `try/except Exception` blocks that
    call `_cleanup()` before re-raising, ensuring the terminal is always restored even on
    unexpected errors.
  - File: `tea.py`

---

## 2. Missing Features

Features present in the Go library that have no Python equivalent.

- [ ] **Add `WithContext` / context-based cancellation**
  - Accept an optional `threading.Event stop_event` in the constructor; check it in the
    event loop timeout poll.
  - File: `tea.py`

- [ ] **Add `WithFilter` / message filtering**
  - Go's `WithFilter(func(Model, Msg) Msg)` lets the program intercept every message
    before it reaches `Update`.
  - Add a `filter: Optional[Callable[[Model, Msg], Optional[Msg]]]` parameter to
    `Program.__init__`; apply it at the top of `_event_loop()`.
  - File: `tea.py`

- [ ] **Add `WithReportFocus` / focus event reporting**
  - `FocusMsg` and `BlurMsg` exist but are never emitted — the input reader does not
    parse focus event escape sequences (`\x1b[I` = focus, `\x1b[O` = blur).
  - Add a `report_focus: bool` constructor parameter; when enabled, write `\x1b[?1004h`
    on setup, parse the sequences in `_start_input_reader`, put `FocusMsg`/`BlurMsg`
    into the queue.
  - Files: `tea.py`, `screen.py`

- [ ] **Add `use_null_renderer` option**
  - Go allows `WithoutRenderer()` to disable all rendering output, useful for headless
    testing.
  - Add a `use_null_renderer: bool` constructor parameter that swaps `Renderer` for
    `NullRenderer`.
  - File: `tea.py`

- [ ] **Add `release_terminal()` / `restore_terminal()`**
  - Go exposes these to temporarily hand the terminal back to the OS (e.g. before opening
    an editor) and reclaim it afterwards.
  - Implement `release_terminal()` (restore termios, stop renderer, disable mouse) and
    `restore_terminal()` (re-enter raw mode, re-enable options, restart renderer, repaint).
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
