# Bubble Tea Python — Commands Tutorial

This tutorial is a deep dive into **commands** (`Cmd`) — how they work,
how to compose them, and when to use each variant.

It mirrors the Go [commands tutorial](../commands/README.md).

---

## What is a command?

A `Cmd` is just a Python callable with the signature:

```python
Callable[[], Optional[Msg]]
```

Commands **always run in a background daemon thread** managed by the
`Program`.  They must not write to `stdout` / `stderr` directly (that
would corrupt the TUI).  Instead they return a `Msg` which the event loop
delivers to `model.update()`.

```python
# A simple command that sleeps and then delivers a message.
def my_cmd() -> Optional[tea.Msg]:
    time.sleep(2)
    return DoneMsg()
```

Return it from `init()` or `update()`:

```python
def init(self):
    return my_cmd          # note: the function itself, not my_cmd()

def update(self, msg):
    ...
    return self, my_cmd    # same here
```

---

## One-shot timer: `tick()`

```python
@dataclass
class BlinkMsg:
    pass

def init(self):
    return tea.tick(0.5, BlinkMsg)   # fire BlinkMsg after 0.5 s

def update(self, msg):
    if isinstance(msg, BlinkMsg):
        self.cursor_visible = not self.cursor_visible
        return self, tea.tick(0.5, BlinkMsg)   # re-subscribe
    return self, None
```

`tick()` fires **once**.  Re-subscribe from `update()` each time to keep it
going.  This is the **re-subscription pattern** — it lets you cancel a timer
simply by not returning `tick()` again.

---

## Repeating timer: `every()`

`every()` is an alias for `tick()` with re-subscription semantics made
explicit in its docstring.  Both fire once per call.

```python
def init(self):
    return tea.every(1.0, TickMsg)

def update(self, msg):
    if isinstance(msg, TickMsg):
        ...
        return self, tea.every(1.0, TickMsg)   # re-subscribe
    return self, None
```

---

## Parallel commands: `batch()`

Run multiple commands at the same time.  All results are delivered to
`update()` independently (no ordering guarantee).

```python
def init(self):
    return tea.batch(
        fetch_users(),
        fetch_config(),
        tea.tick(10.0, TimeoutMsg),
    )
```

`batch()` filters out `None` values and returns `None` if there are no
valid commands.  If only one command remains after filtering, it is returned
directly (no overhead).

---

## Sequential commands: `sequence()`

Run commands one after another.  Each command's result is delivered to
`update()` before the next command starts.

```python
def on_save(self, msg):
    return self, tea.sequence(
        validate(),
        upload(),
        notify_done(),
    )
```

Errors in a step (an exception in the command) stop the sequence and trigger
`ErrProgramPanic`.

---

## Background I/O

Any callable that blocks is fine as a command:

```python
import urllib.request

def fetch_data() -> Optional[tea.Msg]:
    try:
        with urllib.request.urlopen("https://example.com") as r:
            return DataMsg(body=r.read())
    except Exception as exc:
        return ErrMsg(error=exc)

def init(self):
    return fetch_data
```

---

## Sending messages externally

From any thread, call `program.send(msg)` to inject a message:

```python
p = tea.Program(model)

def background_worker():
    while True:
        result = do_work()
        p.send(ResultMsg(result))

threading.Thread(target=background_worker, daemon=True).start()
p.run()
```

---

## Screen-control commands

These are returned from `init()` or `update()` and are handled by the
event loop before `update()` sees them:

```python
tea.enter_alt_screen()          # switch to alternate screen buffer
tea.exit_alt_screen()
tea.hide_cursor()
tea.show_cursor()
tea.enable_mouse_cell_motion()  # track clicks and drags
tea.enable_mouse_all_motion()   # track every mouse movement too
tea.disable_mouse()
tea.clear_screen()
tea.set_window_title("My App")
tea.suspend()                   # ctrl-z equivalent
```

---

## Combining commands

```python
def init(self):
    return tea.batch(
        tea.enter_alt_screen(),
        tea.hide_cursor(),
        tea.window_size(),         # get dimensions immediately
        tea.tick(1.0, TickMsg),
    )
```

---

## External process execution

Temporarily hand the terminal to a subprocess, then resume:

```python
def on_edit(self):
    cmd = tea.ExecCmd(["vim", self.filename])
    return self, tea.exec_process(cmd, self.on_editor_exit)

def on_editor_exit(self, err):
    return EditorDoneMsg(error=err)
```

The TUI is restored automatically after the subprocess exits.

---

## Quitting

| Expression | Effect |
|-----------|--------|
| `return self, tea.quit_cmd` | Graceful quit from inside the model |
| `p.quit()` | Graceful quit from another thread |
| `p.kill()` | Immediate kill (no queue drain) |

```python
# quit_cmd is itself a Cmd:
def update(self, msg):
    if isinstance(msg, tea.KeyMsg) and msg.key == "q":
        return self, tea.quit_cmd
    return self, None
```
