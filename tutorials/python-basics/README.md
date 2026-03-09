# Bubble Tea Python — Basics Tutorial

This tutorial mirrors the Go [basics tutorial](../basics/README.md) but uses the
Python port of Bubble Tea.  It walks you through building a small TUI program
step by step.

---

## Prerequisites

```bash
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"   # from the repo root
```

Python 3.10 or newer is required.

---

## The Elm Architecture in 60 seconds

Every Bubble Tea program has three parts:

| Part | What it does |
|------|-------------|
| **Model** | Holds all program state |
| **Update** | Receives messages, returns new state + next command |
| **View** | Renders the current state as a string |

The runtime loop is:

1. Call `model.init()` — get the first command (if any).
2. Wait for a **message** (key press, timer, HTTP response, …).
3. Call `model.update(msg)` → `(new_model, cmd)`.
4. Render `new_model.view()` to the terminal.
5. Run `cmd` in the background; its return value becomes the next message.
6. Go to step 2.

---

## Step 1 — The simplest possible program

```python
import bubblepy as tea

class Model(tea.Model):
    def init(self):
        return None          # no initial command

    def update(self, msg):
        if isinstance(msg, tea.KeyMsg) and msg.key == "q":
            return self, tea.quit_cmd
        return self, None

    def view(self):
        return "Press q to quit.\n"

tea.Program(Model()).run()
```

Save this as `hello.py` and run it:

```bash
python hello.py
```

Press `q` to exit.

---

## Step 2 — Reacting to key presses

`KeyMsg.key` is a string like `"a"`, `"enter"`, `"ctrl+c"`, `"up"`, `"f1"`.

```python
class Model(tea.Model):
    def __init__(self):
        self.text = ""

    def init(self):
        return None

    def update(self, msg):
        if isinstance(msg, tea.KeyMsg):
            if msg.key == "enter":
                return self, tea.quit_cmd
            elif msg.key == "backspace":
                self.text = self.text[:-1]
            elif len(msg.key) == 1:   # printable character
                self.text += msg.key
        return self, None

    def view(self):
        return f"Type something (Enter to quit):\n> {self.text}_\n"
```

---

## Step 3 — Commands and messages

A **command** is a `Callable[[], Optional[Msg]]` — a function that does I/O
and returns a message.  Commands always run in a background thread.

```python
from dataclasses import dataclass

@dataclass
class TickMsg:
    pass

class CountdownModel(tea.Model):
    def __init__(self, n: int):
        self.n = n

    def init(self):
        return tea.tick(1.0, TickMsg)   # fire TickMsg after 1 second

    def update(self, msg):
        if isinstance(msg, TickMsg):
            self.n -= 1
            if self.n <= 0:
                return self, tea.quit_cmd
            return self, tea.tick(1.0, TickMsg)   # re-subscribe
        if isinstance(msg, tea.KeyMsg) and msg.key in ("q", "ctrl+c"):
            return self, tea.quit_cmd
        return self, None

    def view(self):
        return f"Quitting in {self.n}...\n"

tea.Program(CountdownModel(5)).run()
```

Key points:
- `tea.tick(duration, MsgClass)` returns a one-shot command.
- To keep ticking, return `tea.tick(...)` again from `update()`.
- This is the **re-subscription** pattern from The Elm Architecture.

---

## Step 4 — Multiple commands with `batch()`

Run commands in parallel and receive all results:

```python
def init(self):
    return tea.batch(
        fetch_data_cmd(),
        tea.tick(5.0, TimeoutMsg),
    )
```

Run commands in sequence (one after another):

```python
return self, tea.sequence(step_one(), step_two(), step_three())
```

---

## Step 5 — Window size

Query the terminal size at startup:

```python
def init(self):
    return tea.window_size()   # delivers WindowSizeMsg immediately

def update(self, msg):
    if isinstance(msg, tea.WindowSizeMsg):
        self.width = msg.width
        self.height = msg.height
    ...
```

The program also receives `WindowSizeMsg` automatically whenever the user
resizes the terminal window (SIGWINCH).

---

## Step 6 — Exiting gracefully

| Method | When to use |
|--------|------------|
| `return self, tea.quit_cmd` | Normal exit from inside the model |
| `p.quit()` | Quit from another thread |
| `p.kill()` | Immediate exit, bypass queue |
| ctrl-c / SIGINT | Delivers `InterruptMsg` to `update()`, then raises `ErrInterrupted` |
| ctrl-z (Unix) | `SuspendMsg` → suspend → `ResumeMsg` on resume |

Catch typed exceptions from `run()`:

```python
try:
    p.run()
except tea.ErrInterrupted:
    print("Interrupted by user")
except tea.ErrProgramKilled:
    print("Killed")
except tea.ErrProgramPanic as e:
    print("Crash:", e)
```

---

## Next steps

- [Commands tutorial](../python-commands/README.md) — deep dive into Cmds.
- Browse the [examples/](../../examples/) directory for complete programs.
- Read the [CLAUDE.md](../../CLAUDE.md) for a full API reference.
