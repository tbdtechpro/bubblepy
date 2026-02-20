# bubbletea — Python port (experiment)

This repository is an experiment to explore how feasible it is to translate a non-trivial Go library into idiomatic Python using AI-assisted ("vibe coded") development with minimal direct human authorship of the code itself.

The subject of the translation is [Bubble Tea](https://github.com/charmbracelet/bubbletea), a TUI framework by [Charm](https://charm.sh) built on [The Elm Architecture](https://guide.elm-lang.org/architecture/).

---

## What this is

- A research experiment, not a production library.
- The Python code, commit history, and documentation in this repo are primarily AI-generated. They do not represent the engineering efforts of the human running the experiment.
- The human's contribution is the experimental design, direction, review, and judgement calls — not the code itself.

## What this is not

- A maintained or supported library.
- A replacement for or competitor to the original [Go Bubble Tea](https://github.com/charmbracelet/bubbletea).
- Validated software. No assumptions should be made about correctness, completeness, or fitness for any purpose until independent validation has been done.

---

## Status

Early-stage / alpha. Core Elm Architecture loop (model → update → view) is functional on Unix. Many Go features are not yet ported. See [`MVP_TASKS.md`](MVP_TASKS.md) for the current gap analysis.

---

## Original library

All credit for the design and architecture belongs to the [Charm](https://charm.sh) team.

> [github.com/charmbracelet/bubbletea](https://github.com/charmbracelet/bubbletea)

---

## License

MIT — see [LICENSE](LICENSE).
