# bubblepy

A Python port of [Bubble Tea](https://github.com/charmbracelet/bubbletea), Charm's Go framework for building terminal UIs with [The Elm Architecture](https://guide.elm-lang.org/architecture/). You write a model with `update()` and `view()`; bubblepy runs the event loop, input decoding and rendering.

Pairs with [pygloss](https://github.com/tbdtechpro/pygloss), my port of Lip Gloss, for styling and layout.

---

## About this project

I built bubblepy as an engineering study: can a non-trivial, concurrency-heavy Go library be carried into *idiomatic* Python, rather than transliterated line by line, and what process produces a result you can trust?

I owned the design and the process, and used AI-assisted development (Claude) for much of the implementation:

- **Porting strategy.** The Go source was the reference implementation while I ported module by module. I removed it once the Python side stood on its own.
- **Mapping Go idioms to Python:**
  - goroutines and channels → threads and a thread-safe message queue
  - Go message structs → `@dataclass` messages
  - functional options → `with_*()` helpers
- **Feasibility analysis.** [`PYTHON_FEASIBILITY.md`](PYTHON_FEASIBILITY.md) classifies each Go feature by how hard it is to reproduce faithfully in Python, and explains why.
- **Verification.** 120+ tests cover key and mouse decoding, commands, the renderer, screen control and the `Program` lifecycle. [pygloss](https://github.com/tbdtechpro/pygloss) adds integration tests against bubblepy's renderer.
- **Platform work.** Signal handling covers graceful shutdown (`SIGTERM`) and ctrl-z suspend/resume. I also added basic Windows console support (raw mode via `ctypes`, `msvcrt` input, UTF-8 output), the piece the feasibility analysis rated hardest to port.

---

## Status

Alpha. The core Elm Architecture loop works on Unix:
- model → update → view
- commands: `batch`, `sequence`, `tick`, `every`
- key and mouse input, alt screen, suspend/resume

Windows support is experimental. Many Go features are not yet ported; see [`MVP_TASKS.md`](MVP_TASKS.md) for the current gap analysis.

---

## Original library

All credit for the original design and architecture belongs to the [Charm](https://charm.sh) team. bubblepy is an independent port and is not affiliated with or endorsed by Charm.

> [github.com/charmbracelet/bubbletea](https://github.com/charmbracelet/bubbletea)

---

## Tutorials (Python)

- [Basics](tutorials/python-basics/README.md): Model / Update / View, key handling, tick/re-subscription
- [Commands](tutorials/python-commands/README.md): a deep dive into `Cmd`, `batch`, `sequence` and background I/O

---

## Attribution

See [ATTRIBUTION.md](ATTRIBUTION.md) for full credits: the original Charm team, Evan Czaplicki (The Elm Architecture), and the tooling used to build the port.

---

## License

MIT — see [LICENSE](LICENSE).
