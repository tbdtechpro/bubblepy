# CLAUDE.md

This file provides guidance for AI assistants working in this repository.

## Repository Overview

This repository contains two parallel implementations of the **Bubble Tea** TUI framework:

1. **Go library** (`github.com/charmbracelet/bubbletea`) — the original, battle-tested implementation, production-ready.
2. **Python port** — a Python port of the Go library, mirroring the API in an idiomatic Python style (version 0.1.0, alpha status).

Bubble Tea is a terminal UI framework based on [The Elm Architecture](https://guide.elm-lang.org/architecture/): a model holds state, an update function handles messages, and a view function renders the UI as a string.

---

## Repository Structure

```
bubbletea/
├── # Go source files (root package `tea`)
├── tea.go                  # Core Program struct, event loop, lifecycle
├── tea_init.go             # Program initialization (terminal setup)
├── tea_test.go             # Core integration tests
├── commands.go             # Batch, Sequence, Every, Tick commands
├── commands_test.go        # Command tests
├── options.go              # ProgramOption functional options
├── options_test.go
├── exec.go                 # External process execution (ExecCmd)
├── exec_test.go
├── renderer.go             # renderer interface
├── standard_renderer.go    # Standard TTY renderer
├── nil_renderer.go         # No-op renderer (testing)
├── nil_renderer_test.go
├── screen.go               # Screen control (alt screen, cursor, etc.)
├── screen_test.go
├── focus.go                # Focus/blur event handling
├── mouse.go                # Mouse event types and parsing
├── mouse_test.go
├── key.go                  # Key types and KeyMsg
├── key_sequences.go        # ANSI escape sequence → key mappings
├── key_other.go            # Non-Windows key handling
├── key_windows.go          # Windows key handling
├── key_test.go
├── logging.go              # Debug logging helpers
├── logging_test.go
├── tty.go                  # TTY abstractions
├── tty_unix.go             # Unix TTY implementation
├── tty_windows.go          # Windows TTY implementation
├── inputreader_other.go    # Non-Windows input reading
├── inputreader_windows.go  # Windows input reading
├── signals_unix.go         # SIGWINCH, SIGTSTP handling
├── signals_windows.go      # Windows signal handling
├── go.mod                  # Go module: github.com/charmbracelet/bubbletea, go 1.24
├── go.sum
│
├── # Python port files
├── __init__.py             # Public API exports, __version__ = "0.1.0"
├── tea.py                  # Program class and event loop
├── model.py                # Model ABC (init/update/view)
├── messages.py             # Msg, KeyMsg, MouseMsg, WindowSizeMsg, ClearScreenMsg, etc.
├── keys.py                 # KeyType enum, escape sequence → key name map
├── mouse.py                # MouseButton, MouseAction, MouseEvent, parse_mouse_event
├── commands.py             # Cmd, BatchMsg, SequenceMsg, quit_cmd, batch, sequence, tick, every
├── renderer.py             # Renderer (FPS-capped, thread-safe) and NullRenderer
├── screen.py               # ANSI constants, screen control Cmd factories
├── pyproject.toml          # Python packaging (requires Python 3.10+)
├── setup.py
│
├── # Experiment documentation
├── README.md               # Project overview — describes the vibe-coding experiment
├── MVP_TASKS.md            # Tracked task list: Go→Python feature parity gaps
├── PYTHON_FEASIBILITY.md   # Analysis of Go features that are hard/infeasible in Python
│
├── examples/               # Go example programs (each in own subdirectory)
│   ├── go.mod              # Separate Go module for examples
│   ├── basics.py           # Python basics example
│   └── <name>/
│       ├── main.go
│       └── README.md
│
├── tutorials/
│   ├── basics/             # Basic tutorial (Go)
│   └── commands/           # Commands tutorial (Go)
│
├── Taskfile.yaml           # Task runner (Go: lint + test)
├── .golangci.yml           # golangci-lint v2 config
└── .github/workflows/      # CI: build, lint, examples, coverage, release
```

---

## The Elm Architecture (Core Concept)

Every Bubble Tea program implements three methods on a **Model**:

| Method | Go signature | Python signature |
|--------|-------------|-----------------|
| `Init` | `Init() Cmd` | `init(self) -> Optional[Cmd]` |
| `Update` | `Update(Msg) (Model, Cmd)` | `update(self, msg) -> Tuple[Model, Optional[Cmd]]` |
| `View` | `View() string` | `view(self) -> str` |

- **Messages** (`Msg`) are values produced by I/O (key presses, timers, HTTP responses).
- **Commands** (`Cmd`) are functions that perform I/O and return a `Msg` when done.
- The program runs `Init`, then loops: receive `Msg` → call `Update` → call `View` to re-render.

---

## Go Development

### Running Tests

```bash
go test ./...
```

Or via Task:

```bash
task test
```

### Running the Linter

```bash
task lint
# equivalent to:
golangci-lint run
```

### Linter Configuration (`.golangci.yml`)

- **Version**: golangci-lint v2
- **Formatters**: `gofumpt`, `goimports` (use these, not plain `gofmt`)
- **Enabled linters**: `bodyclose`, `exhaustive`, `goconst`, `godot`, `gosec`, `misspell`, `nestif`, `nilerr`, `revive`, `unconvert`, `unparam`, `whitespace`, `wrapcheck`, and others
- Tests are excluded from linting (`run.tests: false`)
- Max issues per linter: unlimited (0)

### Key Go Conventions

- All exported types, functions, and variables must have godoc comments ending in a period (enforced by `godot`).
- Use `//nolint:lintername` with a comment when suppressing a linter, not `--no-verify`.
- Error wrapping: use `fmt.Errorf("%w: %w", outerErr, innerErr)` pattern (see `tea.go`).
- Signal handling: `SIGINT` sends `InterruptMsg`; `SIGTERM` sends `QuitMsg`.
- Panics are caught by default and result in `ErrProgramPanic`; use `WithoutCatchPanics()` to disable.
- Platform-specific code uses `_unix.go` / `_windows.go` / `_other.go` suffixes.

### Go Key Types

- `Model` — interface with `Init()`, `Update()`, `View()`
- `Cmd` — `func() Msg`
- `Msg` — `interface{}`
- `Program` — created with `NewProgram(model, opts...)`, started with `p.Run()`
- `BatchMsg` — `[]Cmd`, used by `Batch()`
- `QuitMsg`, `InterruptMsg`, `SuspendMsg`, `ResumeMsg` — lifecycle messages

### Go Program Options

Pass to `NewProgram()`:

```go
tea.WithAltScreen()
tea.WithMouseCellMotion()
tea.WithMouseAllMotion()
tea.WithInput(r)           // custom input reader
tea.WithOutput(w)          // custom output writer
tea.WithContext(ctx)
tea.WithFPS(fps)
tea.WithoutSignalHandler()
tea.WithoutCatchPanics()
tea.WithReportFocus()
```

### Examples (Go)

Each example lives in `examples/<name>/main.go` under a separate Go module (`examples/go.mod`). Run any example with `go run ./examples/<name>`.

---

## Python Development

### Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

### Running Tests

```bash
pytest
```

### Code Style

- **Formatter**: `black` (line length 100)
- **Import sorting**: `isort` (black profile)
- **Type checking**: `mypy` (strict, `disallow_untyped_defs = true`)
- **Linting**: `flake8`
- Python 3.10+ required; use `match`/`isinstance` for message dispatch.

### Python Key Types

- `Model` — abstract base class in `model.py`; implement `init()`, `update()`, `view()`
- `Cmd` — `Callable[[], Optional[Msg]]` (from `commands.py`)
- `Msg` — base class in `messages.py`
- `Program` — in `tea.py`; start with `p.run()`

### Python Program Constructor

```python
import bubbletea as tea

p = tea.Program(
    model,
    alt_screen=False,
    mouse_cell_motion=False,
    mouse_all_motion=False,
    bracketed_paste=False,
    fps=60,
)
final_model = p.run()
```

### Python Message Types

| Class | Key attributes | Notes |
|-------|---------------|-------|
| `KeyMsg` | `key: str`, `alt: bool` | |
| `MouseMsg` | `x`, `y`, `button`, `action`, `alt`, `ctrl`, `shift` | |
| `WindowSizeMsg` | `width: int`, `height: int` | |
| `FocusMsg` | — | Defined but not yet emitted by input reader |
| `BlurMsg` | — | Defined but not yet emitted by input reader |
| `QuitMsg` | — | |
| `ClearScreenMsg` | — | Handled by event loop → `renderer.clear()` |
| `SetWindowTitleMsg` | `title: str` | Handled by event loop → `renderer.set_window_title()` |
| `BatchMsg` | `cmds: list` | Internal — produced by `batch()`, consumed by event loop |
| `SequenceMsg` | `cmds: list` | Internal — produced by `sequence()`, consumed by event loop |

### Python Commands

```python
# Quit
return model, tea.quit_cmd

# Concurrent commands — all run in parallel, all messages delivered
cmd = tea.batch(cmd1, cmd2)

# Sequential commands — run in order, all messages delivered
cmd = tea.sequence(cmd1, cmd2)

# One-shot delayed message
cmd = tea.tick(1.0, lambda: MyMsg())

# Repeating tick — fires once; return from update() to re-subscribe
cmd = tea.every(1.0, lambda: MyMsg())

# Screen control (return from update or init)
tea.enter_alt_screen()
tea.exit_alt_screen()
tea.hide_cursor()
tea.show_cursor()
tea.enable_mouse_cell_motion()
tea.enable_mouse_all_motion()
tea.disable_mouse()
tea.clear_screen()
tea.set_window_title("My App")
```

### Python vs Go Naming

| Go | Python |
|----|--------|
| `tea.NewProgram(m)` | `tea.Program(m)` |
| `p.Run()` | `p.run()` |
| `tea.Quit` | `tea.quit_cmd` |
| `tea.Batch(...)` | `tea.batch(...)` |
| `tea.Sequence(...)` | `tea.sequence(...)` |
| Type switch | `isinstance(msg, tea.KeyMsg)` |

---

## CI / GitHub Actions

Workflows in `.github/workflows/` delegate to reusable workflows from `charmbracelet/meta`:

| Workflow | Trigger | Purpose |
|----------|---------|---------|
| `build.yml` | push/PR | Build Go (root + examples) |
| `lint.yml` | push/PR | Run golangci-lint |
| `examples.yml` | push/PR | Build/test examples |
| `coverage.yml` | push/PR | Code coverage |
| `release.yml` | tag | Release automation |

---

## Debugging

### Go

Bubble Tea takes over the terminal; use the built-in file logger:

```go
f, _ := tea.LogToFile("debug.log", "debug")
defer f.Close()
```

Then `tail -f debug.log` in another terminal.

### Python

Log to a file (stdout is the TUI):

```python
import logging
logging.basicConfig(filename="debug.log", level=logging.DEBUG)
logging.debug(f"msg: {msg}")
```

Then `tail -f debug.log` in another terminal.

---

## Important Notes for AI Assistants

- **Two separate implementations exist side by side.** Go files are at the root; Python files are also at the root but identified by `.py` extension. They implement the same concepts with language-appropriate idioms.
- **Go module path**: `github.com/charmbracelet/bubbletea`. Do not change this.
- **Examples have their own Go module** at `examples/go.mod` — they must be modified separately from the root module.
- **This repo is an experiment.** The Python port is AI-generated and unvalidated. See `README.md`. Do not represent it as production-ready.
- **The Python port is alpha** (v0.1.0). Windows support is not yet implemented. Focus reporting, bracketed paste, `exec_process()`, and `WithFilter` are all implemented. See `PYTHON_FEASIBILITY.md` for features that are structurally difficult to port.
- **Never log to stdout/stderr** in a running TUI program — it will corrupt the display. Always use file logging.
- **Terminal raw mode** is set during `Program.run()` / `p.Run()`. If a program crashes without cleanup, the terminal may be left in raw mode; restore with `reset` or `stty sane`.
- **Python `Renderer` is FPS-capped and thread-safe.** `render()` queues a pending view; a daemon ticker thread flushes at most `fps` times per second. `start()` must be called before any `render()` call (done automatically by `Program.run()`). `close()` stops the ticker and does a final flush.
- **`batch()` and `sequence()` work via message dispatch.** `batch()` returns a `Cmd` that produces `BatchMsg`; `sequence()` returns one that produces `SequenceMsg`. The event loop handles both — do not pattern-match on these types in model code.
- When writing Go code, prefer `tea.Batch()` for concurrent commands and `tea.Sequence()` for ordered execution.
- The `filter` parameter on `Program` (Python `filter=`, Go `WithFilter`) intercepts all messages before they reach `Update` — useful for testing.
