# Python Bubble Tea — MVP Task List

Tasks required to bring the Python port to feature parity with the Go library for MVP status.
Items are grouped by area and ordered by priority within each group.

---

## 1. Core Event Loop & Program Correctness

These are bugs or missing wiring in the current implementation that affect correctness.

1. **Fix `batch()` to execute commands concurrently**
   - Current implementation uses a duck-typed `_batch_cmds` attribute and iterates sequentially inside `_execute_cmd`.
   - Replace with proper concurrent execution using `threading.Thread` for each command, feeding all results into the message queue — matching Go's goroutine-per-command behaviour.
   - File: `commands.py`, `tea.py`

2. **Fix `sequence()` to emit all messages**
   - Current implementation returns after the first non-None result, silently dropping subsequent messages.
   - Must emit one message per command, in order, waiting for each to complete before starting the next.
   - File: `commands.py`, `tea.py`

3. **Handle `ClearScreenMsg` in the event loop**
   - `clear_screen()` command exists in `commands.py` and produces a `ClearScreenMsg`, but `Program._event_loop()` never matches it — the message falls through to `model.update()` unhandled.
   - Add handling in `_event_loop()` that calls `self._renderer.clear()`.
   - File: `tea.py`

4. **Handle `WindowTitleMsg` in the event loop**
   - Same problem as `ClearScreenMsg`: `set_window_title()` produces a `WindowTitleMsg` that the event loop ignores.
   - Add handling that calls `self._renderer.set_window_title(msg.title)`.
   - File: `tea.py`

5. **Fix `every()` to repeat indefinitely**
   - Current `every()` just delegates to `tick()` and fires once, then stops.
   - Implement a looping command that sleeps for the interval, emits the message, then re-schedules itself (returns a new `every()` command) so the runtime keeps it alive.
   - File: `commands.py`

6. **Add FPS-controlled rendering**
   - The `fps` parameter is accepted by `Program.__init__` and passed to `Renderer`, but the renderer never enforces a frame rate — it re-renders on every update.
   - Add a `threading.Timer` or `time.sleep`-based tick inside the renderer so frames are only flushed at most `fps` times per second, batching intermediate renders (matching Go's `standardRenderer` ticker behaviour).
   - File: `renderer.py`

7. **Wire up SIGTERM for graceful shutdown**
   - `_setup_signals()` only registers `SIGWINCH` (window resize). `SIGTERM` (e.g. from `kill <pid>`) is not caught, leaving the terminal in raw mode on unexpected exit.
   - Register a `SIGTERM` handler that sends `QuitMsg` through the message queue.
   - File: `tea.py`

8. **Add `SuspendMsg` / `ResumeMsg` and SIGTSTP handling**
   - Go supports `SuspendMsg` (triggered by `Suspend()` or Ctrl-Z), which pauses the TUI, sends `SIGTSTP`, and resumes on `SIGCONT`, emitting `ResumeMsg`.
   - Add `SuspendMsg` and `ResumeMsg` dataclasses to `messages.py`.
   - In `_event_loop()` handle `SuspendMsg`: restore terminal, send `SIGTSTP` to self, wait for `SIGCONT`, re-enter raw mode, emit `ResumeMsg`.
   - Export from `__init__.py`.
   - Files: `messages.py`, `tea.py`, `__init__.py`

9. **Add `Program.kill()` for immediate shutdown**
   - `Program.quit()` sends `QuitMsg` (graceful). `kill()` should set the quit event and skip the final render — equivalent to Go's `Program.Kill()` which calls `p.cancel()` directly.
   - File: `tea.py`

10. **Add `Program.wait()` to block until the program exits**
    - Go's `Program.Wait()` blocks until shutdown is complete, useful when driving the program from a separate thread.
    - Implement using a `threading.Event` that is set at the end of `run()`.
    - File: `tea.py`

11. **Add `Program.println()` / `Program.printf()` to print above the TUI**
    - Go's `Program.Println()` / `Program.Printf()` inject a `printLineMessage` that the renderer outputs above the managed TUI area, persisting across re-renders.
    - Add equivalents that enqueue a print message handled before the next frame.
    - Files: `tea.py`, `renderer.py`

---

## 2. Missing Features

Features present in the Go library that have no Python equivalent.

12. **Add `WithContext` / context-based cancellation**
    - Accept a `threading.Event` or Python `contextvars` / `asyncio` cancellation token so an external caller can cancel the program without calling `Program.kill()` directly.
    - Simplest approach: accept an optional `threading.Event stop_event` in the constructor; check it in the event loop timeout poll.
    - File: `tea.py`

13. **Add `WithFilter` / message filtering**
    - Go's `WithFilter(func(Model, Msg) Msg)` lets the program intercept every message before it reaches `Update`, allowing e.g. global keybinding interception or event logging.
    - Add a `filter: Optional[Callable[[Model, Msg], Optional[Msg]]]` parameter to `Program.__init__`; apply it at the top of `_event_loop()`.
    - File: `tea.py`

14. **Add `WithReportFocus` / focus event reporting**
    - The `FocusMsg` and `BlurMsg` classes exist but are never emitted — the input reader does not parse focus event escape sequences (`\x1b[I` = focus, `\x1b[O` = blur`).
    - Add a `report_focus: bool` constructor parameter; when enabled, write `\x1b[?1004h` on setup, parse the focus/blur sequences in `_start_input_reader`, and put `FocusMsg`/`BlurMsg` into the queue.
    - Files: `tea.py`, `screen.py`

15. **Add `WithoutRenderer` option**
    - Go allows `WithoutRenderer()` to disable all rendering output, useful for headless testing.
    - Add a `use_null_renderer: bool` constructor parameter that swaps `Renderer` for `NullRenderer`.
    - Files: `tea.py`

16. **Add `ReleaseTerminal()` / `RestoreTerminal()`**
    - Go exposes these to temporarily hand the terminal back to the OS (e.g. before opening an editor) and reclaim it afterwards.
    - Implement `release_terminal()` (restore termios, stop renderer, disable mouse) and `restore_terminal()` (re-enter raw mode, re-enable options, restart renderer, repaint).
    - File: `tea.py`

17. **Implement `exec_process()` for external command execution**
    - Go's `ExecProcess(cmd, callback)` suspends the TUI, runs an interactive subprocess (editor, shell, etc.) with full terminal access, then resumes and delivers the error via a message.
    - Implement using `subprocess.Popen` with `stdin=sys.stdin`, `stdout=sys.stdout`, `stderr=sys.stderr` after calling `release_terminal()`, with `restore_terminal()` in a `finally` block.
    - Add `ExecCmd` abstract base class, `exec_process()` command factory.
    - Files: `exec.py` (new), `tea.py`, `__init__.py`

18. **Add `log_to_file()` debug logging helper**
    - Since the TUI occupies stdout, users cannot use `print()` for debugging. Go provides `LogToFile(path, prefix)` to redirect the standard logger to a file.
    - Implement `log_to_file(path: str, prefix: str = "") -> logging.FileHandler` that configures Python's `logging` module root handler to write to the given file.
    - Files: `logging.py` (new), `__init__.py`

19. **Add `Program.set_window_title()` method**
    - Go's `Program.SetWindowTitle(title)` lets callers change the title imperatively from outside the update loop.
    - Add a public method that sends `WindowTitleMsg` through the message queue.
    - File: `tea.py`

20. **Add bracketed paste support**
    - Go supports `WithoutBracketedPaste()` (it's on by default) and emits `PasteMsg` / `PasteStartMsg` / `PasteEndMsg`.
    - Add `PasteMsg`, `PasteStartMsg`, `PasteEndMsg` dataclasses to `messages.py`.
    - Parse bracketed paste sequences (`\x1b[200~`...`\x1b[201~`) in the input reader when `bracketed_paste=True`.
    - Export from `__init__.py`.
    - Files: `messages.py`, `tea.py`, `__init__.py`

---

## 3. Test Suite

The Python port has zero test coverage. Every module needs tests.

21. **Create `tests/` directory with `conftest.py` and pytest fixtures**
    - Set up shared fixtures: `null_renderer`, `test_program(model)` factory that uses `NullRenderer` and pre-loaded messages, `capture_queue` helper.
    - File: `tests/conftest.py` (new)

22. **Write unit tests for `keys.py`**
    - Test `parse_key()` for: printable ASCII, control characters (ctrl+c, ctrl+a, etc.), all arrow/navigation keys, function keys f1–f12, alt+key sequences, multi-byte UTF-8, empty/unknown sequences.
    - Should mirror the scope of Go's `key_test.go` (which contains 100+ table-driven cases).
    - File: `tests/test_keys.py` (new)

23. **Write unit tests for `mouse.py`**
    - Test `parse_mouse_event()` for: SGR press/release/motion, wheel up/down/left/right, all modifier combinations (alt, ctrl, shift), coordinate conversion, X10 fallback, malformed sequences.
    - File: `tests/test_mouse.py` (new)

24. **Write unit tests for `commands.py`**
    - Test `quit_cmd` returns `QuitMsg`.
    - Test `batch()`: nil filtering, single-command passthrough, concurrent execution (verify commands run in parallel using timing), all results delivered to queue.
    - Test `sequence()`: commands run in order (use a shared list to record order), all messages delivered.
    - Test `tick()`: message is delivered after the specified delay.
    - Test `every()`: message fires repeatedly (at least 3 times in a timeout window).
    - File: `tests/test_commands.py` (new)

25. **Write unit tests for `renderer.py`**
    - Test `Renderer.render()`: first render writes content, identical re-render is skipped, changed content clears and rewrites.
    - Test alt screen enter/exit sequences are emitted.
    - Test cursor hide/show sequences.
    - Test mouse enable/disable sequences.
    - Test `NullRenderer` methods are all no-ops (no output written).
    - File: `tests/test_renderer.py` (new)

26. **Write unit tests for `screen.py`**
    - Test each command factory (`enter_alt_screen`, `exit_alt_screen`, `hide_cursor`, etc.) returns a `Cmd` that produces the correct message type.
    - File: `tests/test_screen.py` (new)

27. **Write integration tests for `Program` lifecycle**
    - Test that `init()` command is executed and its message reaches `update()`.
    - Test that `quit_cmd` returned from `update()` causes `run()` to return the final model.
    - Test `Program.send()` injects a message that is processed by `update()`.
    - Test `Program.kill()` exits immediately.
    - Test `WindowSizeMsg` is delivered on `SIGWINCH`.
    - Test `WithFilter` intercepts and drops messages.
    - File: `tests/test_program.py` (new)

28. **Write unit tests for `logging.py`** (once implemented)
    - Test `log_to_file()` creates the file, appends on subsequent calls, and directs `logging.debug()` output to the file.
    - File: `tests/test_logging.py` (new)

---

## 4. Packaging & Type Safety

29. **Add `py.typed` marker file (PEP 561)**
    - An empty `py.typed` file signals to mypy and other type checkers that the package ships inline types.
    - File: `py.typed` (new)

30. **Fix `__all__` to include `__version__`**
    - `__version__ = "0.1.0"` is defined in `__init__.py` but not listed in `__all__`.
    - Add `"__version__"` to the `__all__` list.
    - File: `__init__.py`

31. **Add `py.typed` to `pyproject.toml` package data**
    - Ensure `py.typed` is included in the distribution.
    - Add `[tool.setuptools.package-data] bubbletea = ["py.typed"]` to `pyproject.toml`.
    - File: `pyproject.toml`

32. **Run `mypy` over all Python source files and fix all errors**
    - The `pyproject.toml` requires `disallow_untyped_defs = true`. Several places use `# type: ignore` comments for the duck-typed `_batch_cmds`/`_sequence_cmds` attributes — these should be eliminated once the batch/sequence fixes (tasks 1 and 2) land.
    - File: all `.py` files

33. **Ensure all public symbols are exported from `__init__.py`**
    - Audit and add any missing exports: `SuspendMsg`, `ResumeMsg`, `PasteMsg`, `PasteStartMsg`, `PasteEndMsg`, `ExecCmd`, `exec_process`, `log_to_file`, `every`, `tick`.
    - File: `__init__.py`

---

## 5. CI / GitHub Actions

34. **Add Python lint + test workflow**
    - Create `.github/workflows/python.yml` that runs on push/PR.
    - Steps: `pip install -e ".[dev]"`, `black --check .`, `isort --check .`, `flake8`, `mypy bubbletea/`, `pytest --cov=bubbletea tests/`.
    - File: `.github/workflows/python.yml` (new)

35. **Add Python coverage reporting**
    - Configure `pytest-cov` to output a coverage report and fail if coverage drops below a threshold (e.g. 80%).
    - Add `[tool.coverage.run]` and `[tool.coverage.report]` sections to `pyproject.toml`.
    - File: `pyproject.toml`

---

## 6. Examples

36. **Port the `simple` example (countdown timer)**
    - Minimal Bubble Tea program: counts down from 5, exits when it reaches 0.
    - Demonstrates `tick()` command and `WindowSizeMsg`-independent layout.
    - File: `examples/simple.py` (new)

37. **Port the `http` example (async HTTP request)**
    - Fetches a URL in a `Cmd` using `urllib.request` or `http.client`, displays a spinner while loading, shows the result.
    - Demonstrates async commands and custom message types.
    - File: `examples/http.py` (new)

38. **Port the `mouse` example (mouse event display)**
    - Renders the last mouse event (button, position, modifiers) in the terminal as the user moves the mouse and clicks.
    - Demonstrates `mouse_all_motion=True` and `MouseMsg` handling.
    - File: `examples/mouse.py` (new)

39. **Port the `realtime` example (real-time updates)**
    - Uses a background thread that sends messages to a running `Program` via `Program.send()`, demonstrating external message injection.
    - Demonstrates `Program.send()` and `every()`/threading.
    - File: `examples/realtime.py` (new)

40. **Port the `send-msg` example**
    - Launches a `Program` in a thread, then sends it messages from the main thread using `Program.send()`.
    - File: `examples/send_msg.py` (new)

41. **Port the `exec` example (launch external editor)**
    - Opens `$EDITOR` (or `vi`) on a temp file, then reads and displays the file contents after the editor exits.
    - Demonstrates `exec_process()`.
    - File: `examples/exec.py` (new)

42. **Port the `views` example (multiple views / screens)**
    - Multiple distinct view states managed in the model; demonstrates switching between views.
    - File: `examples/views.py` (new)

43. **Update `examples/README.md` to document Python examples**
    - List each Python example with a one-line description and how to run it.
    - File: `examples/README.md`

---

## 7. Documentation

44. **Complete `Contributing.md` with Python developer workflow**
    - Add: virtual environment setup, `pip install -e ".[dev]"`, running `pytest`, `mypy`, `black`, `isort`, PR conventions, how to add a new example.
    - File: `Contributing.md`

45. **Write Python tutorial — basics**
    - A step-by-step tutorial matching `tutorials/basics/README.md` but written for the Python API, walking through the shopping list example.
    - File: `tutorials/python-basics/README.md` (new)

46. **Write Python tutorial — commands**
    - A step-by-step tutorial matching `tutorials/commands/README.md` but using Python's `Cmd` type, `tick()`, and `every()`.
    - File: `tutorials/python-commands/README.md` (new)
