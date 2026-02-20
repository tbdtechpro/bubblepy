# Python Port — Feasibility Analysis

This document analyses elements of the Go Bubble Tea library that are difficult or
impossible to replicate faithfully in a Python port.  It is written to support an honest
assessment of the experiment's limits, not to encourage work-arounds.

Items are grouped by severity.

---

## 1. Effectively infeasible

These features cannot be replicated in Python without losing the essential property the Go
implementation relies on.

### 1.1 True concurrency — goroutines and channels

Go's event loop spawns independent goroutines for input reading, signal handling, command
execution, and rendering. They communicate via typed channels with `select`, achieving
true OS-thread parallelism at minimal cost (a goroutine is ~2 KB; a Python thread is
~8 MB, and the GIL prevents bytecode-level parallelism anyway).

`tea.go` runs at least four concurrent goroutines simultaneously without coordination
overhead. Python threads provide the API but not the performance model, and `asyncio`
would require redesigning every callsite that currently returns a `Cmd` value.

**Bottom line:** A Python port can approximate the *behaviour* of the event loop but
cannot match its performance or structural simplicity. Under sustained load (many
concurrent commands, high FPS) the difference will be measurable.

### 1.2 Windows Console API

The Windows path in Bubble Tea reads input through `ReadConsoleInput` / `PeekConsoleInput`
(not stdin), configures console modes via `SetConsoleMode`, and maps Windows Virtual Key
codes to key types. This is direct Win32 API work using `golang.org/x/sys/windows`.

Python has no standard library support for the Windows Console API. The only route is
`ctypes` calling `kernel32.dll` manually, defining every struct by hand. The result is
fragile, untestable without a Windows host, and maintenance-heavy. The existing Python
files do not implement any of this, and there is no realistic path to a well-tested
implementation without dedicated Windows work outside an AI-assisted workflow.

**Bottom line:** The Python port is Unix-only for the foreseeable future.

---

## 2. Hard — significant design work required

These features are reachable but require non-trivial effort and may introduce reliability
problems that the Go version does not have.

### 2.1 Cancellable input reading (CancelReader)

On Unix, Go uses `github.com/muesli/cancelreader` to interrupt a blocking `read()` call
cleanly when the program shuts down — without data loss or race conditions. The read loop
goroutine blocks on I/O; another goroutine signals cancellation; the read returns
immediately with `ErrCanceled`.

Python's `sys.stdin.read()` cannot be interrupted this way. The current port works around
this with `select()` and a 0.1 s timeout, which means shutdown takes up to 100 ms and
the polling wastes CPU. A cleaner solution using `os.pipe()` as a wake-up mechanism is
possible but adds meaningful complexity.

### 2.2 Framerate-capped rendering

`standard_renderer.go` uses `time.Ticker` firing at a configurable FPS (default 60) to
batch view updates into fixed-interval redraws. Rendering happens in a dedicated
goroutine separate from the update loop.

Python's `time.sleep()` precision under load is poor (typically ±10–15 ms on Linux, worse
on macOS), and the GIL means the render thread competes with the update thread even for
CPU-bound work. A 60 FPS target (16.6 ms per frame) is within the noise floor of Python
sleep accuracy. The practical ceiling for a Python TUI renderer is closer to 30 FPS
before timing jitter becomes visible.

### 2.3 Process suspension (SIGTSTP / SIGCONT)

When the user presses `ctrl+z`, Go sends SIGTSTP to the entire process group, restores
the terminal, suspends, then on SIGCONT re-enters raw mode and redraws. This requires
`syscall.Kill(0, syscall.SIGTSTP)` — sending to process group 0.

Python's `signal` module can register SIGTSTP and SIGCONT handlers, but re-raising
SIGTSTP to the process group safely while the terminal restore has already run requires
careful sequencing. More importantly, this is Unix-only and has no equivalent path on
Windows.

### 2.4 External process execution with terminal handoff (Exec / ExecProcess)

`exec.go` implements a clean terminal hand-off: the renderer stops, bracketed paste and
alt-screen state is saved, the terminal is restored to cooked mode, the subprocess runs
with the real stdin/stdout attached, then on return everything is reinstated and the view
redraws.

Python's `subprocess` module can run processes with inherited file descriptors, but the
surrounding machinery — cancelling the input reader, stopping the renderer, saving and
restoring all terminal state atomically, then restarting — requires the same careful
sequencing as the Go version and has more failure modes because each step is a separate
Python call rather than a coordinated goroutine shutdown.

### 2.5 Escape sequence disambiguation

Distinguishing a bare ESC keypress from the start of a multi-byte escape sequence
requires reading ahead with a timeout: if no further bytes arrive within ~50 ms, treat it
as ESC. Go does this implicitly because the read loop runs in its own goroutine and can
use `time.After` in a `select`. In Python, implementing the same timeout without blocking
the whole event loop requires a separate thread or `select()` with a deadline, both of
which add complexity.

The current Python key parser does not implement this and will misread bare ESC presses
as incomplete sequences.

---

## 3. Tedious but straightforward

These are gaps that require work but are structurally compatible with Python.

### 3.1 Bracketed paste detection

The Go parser detects `\x1b[200~` / `\x1b[201~` markers and treats everything between
them as literal text, bypassing key mapping. This is a self-contained parsing change that
can be added to `keys.py`.

### 3.2 Focus / blur reporting

`focus.go` defines `FocusMsg` / `BlurMsg` and the ANSI sequences that enable/disable
focus events (`\x1b[?1004h` / `\x1b[?1004l`). Both message types already exist in the
Python `messages.py`; they just need to be emitted by the input parser when the
corresponding escape sequences are received.

### 3.3 `InterruptMsg` and error return types

Go distinguishes `QuitMsg` (clean exit), `InterruptMsg` (SIGINT / ctrl+c), and fatal
errors (`ErrProgramPanic`, `ErrProgramKilled`, `ErrInterrupted`). The Python port
currently collapses all exit paths. Adding the distinction is a small, contained change.

### 3.4 Rendering thread safety

`standard_renderer.go` wraps all buffer access in a mutex. The Python `Renderer` has no
lock. Adding `threading.Lock` around the render buffer is a one-line change per method.

### 3.5 `LogToFile` debug helper

Go provides `tea.LogToFile(path, prefix)` to redirect the standard logger to a file
before the TUI takes over stdout. Python's `logging` module can do the same; it is just
not exposed as a convenience function yet.

### 3.6 `Println` / `Printf` (print above the TUI)

Go's `Program.Println()` queues lines to be printed above the current view on the next
render. The renderer handles them in `flush()` via `queuedMessageLines`. Python's
renderer has no equivalent but the mechanism is simple to add.

---

## 4. Architectural notes for future work

**Async vs threads.** The current port uses `threading.Thread` for command execution.
An `asyncio`-based port would better match Go's goroutine model for I/O-bound commands,
but would require the user's `Model.update()` and `Model.init()` to be async functions,
which is a breaking API change and may be surprising for users who just want to write a
small TUI.

**The GIL and rendering.** If the Python port is ever profiled under load, the most
likely bottleneck is the render thread competing with the update thread under the GIL.
The practical fix is to make the render buffer a `bytearray` written in one GIL-released
`os.write()` call rather than multiple small `sys.stdout.write()` calls.

**Windows.** Any Windows support would most likely be built on top of a library like
`windows-curses` or `pywinpty` rather than raw `ctypes` calls. Neither matches the
fidelity of the Go implementation.

---

## Summary

| Area | Verdict |
|------|---------|
| Core Elm loop (model → update → view) | Feasible — already works |
| Unix terminal raw mode | Feasible — `termios` module sufficient |
| Concurrent command execution | Approximable — threads work, not goroutines |
| Framerate rendering | Approximable — ~30 FPS realistic ceiling |
| Key / mouse parsing | Feasible — tedious, largely done |
| Focus / blur / bracketed paste | Feasible — straightforward additions |
| Cancellable input reading | Hard — current polling approach good enough for MVP |
| Escape sequence disambiguation | Hard — needs timeout machinery |
| Process suspension (ctrl+z) | Hard — Unix only, requires sequencing care |
| External process execution | Hard — possible but fragile |
| Windows support | Effectively infeasible without dedicated non-AI work |
| True goroutine-level concurrency | Infeasible — structural difference between languages |
