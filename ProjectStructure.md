# Project Structure

See [`CLAUDE.md`](CLAUDE.md) for the full annotated file tree, key types, naming
conventions, and notes for AI assistants.

## Python source files (root level)

| File | Purpose |
|------|---------|
| `__init__.py` | Public API exports, `__version__` |
| `tea.py` | `Program` class, event loop, terminal setup |
| `model.py` | `Model` abstract base class |
| `messages.py` | All message types (`KeyMsg`, `MouseMsg`, `ClearScreenMsg`, etc.) |
| `keys.py` | Key parsing, `KeyType` enum |
| `mouse.py` | Mouse event parsing, `MouseButton`, `MouseAction` |
| `commands.py` | `Cmd`, `BatchMsg`, `SequenceMsg`, `batch()`, `sequence()`, `tick()`, `every()` |
| `renderer.py` | FPS-capped, thread-safe `Renderer` and `NullRenderer` |
| `screen.py` | Screen control command factories (`enter_alt_screen`, etc.) |

## Experiment documentation

| File | Purpose |
|------|---------|
| `README.md` | Project overview — describes the vibe-coding experiment |
| `MVP_TASKS.md` | Tracked task list: Go→Python feature parity gaps |
| `PYTHON_FEASIBILITY.md` | Analysis of Go features that are hard/infeasible in Python |
| `CLAUDE.md` | Detailed guide for AI assistants working in this repo |
| `Contributing.md` | Developer workflow and contribution notes |
