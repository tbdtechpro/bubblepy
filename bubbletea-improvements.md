# bubbletea — Renderer & App Integration Issues
# Source: discovered while building KeroGrid with bubbletea + lipgloss
#
# COPY TARGET: append this block to MVP_TASKS.md in tbdtechpro/bubbletea
# as a new top-level section.
# ─────────────────────────────────────────────────────────────────────────────

---

## 8. Renderer Correctness & App Integration

Bugs and missing behaviours discovered while building a multi-field form
application (KeroGrid) against the Python port. Items are ordered by the
severity of their visible impact on app developers.

- [ ] **Renderer: convert `\n` to `\r\n` when writing the view in raw mode**
  - `tty.setraw()` disables `OPOST`/`ONLCR`. In raw mode `\n` is a pure line
    feed — it moves the cursor down one row but does **not** return it to column 0.
    The renderer calls `self.output.write(view)` directly, so every line after
    the first is written starting at the column where the previous line ended.
    The layout renders as a staircase or overlapping garbage.
  - The Go port handles this internally. The print-line path already uses
    `"\r\n"` correctly; the view path does not.
  - **Fix:** convert the view string to `\r\n` line endings before writing:
    ```python
    self.output.write(view.replace("\n", "\r\n"))
    ```
    This is safe whether ONLCR is active or not (an extra `\r` before `\r\n`
    is harmless on any terminal).
  - Files: `renderer.py` (`_flush`)

- [ ] **Renderer: write `\r` before each new frame to reset cursor column**
  - After the erase sequence (`"\x1b[A\x1b[2K" * _lines_rendered`) the cursor
    is at row 0 of the previous frame but at an **arbitrary column** — whatever
    column the last written line ended at. The new view is then written from
    that column, producing a rightward-drifting re-render on every keystroke.
  - **Fix:** write `\r` immediately before the new view:
    ```python
    self.output.write("\r" + view.replace("\n", "\r\n"))
    ```
    Alternatively use `\x1b[H` (cursor home) when in alt-screen mode for an
    absolute position reset.
  - Files: `renderer.py` (`_flush`)

- [ ] **Renderer: enforce or auto-correct trailing `\n` on view strings**
  - `_lines_rendered = view.count("\n")`. This count drives the erase-upward
    loop on the next frame.
  - If a view has N lines joined by `\n` with **no trailing newline**: count
    is N−1. The erase lands on line 2 instead of line 1, and the entire UI
    drifts down by one line per redraw.
  - If the view ends with `\n` (cursor on a blank line N+1): count is N and
    the erase lands exactly on line 1. All working examples use this pattern.
  - The contract is nowhere documented and not enforced.
  - **Fix (recommended):** auto-append `\n` if the view does not already end
    with one, so apps are not silently broken by the omission:
    ```python
    if not view.endswith("\n"):
        view += "\n"
    self._lines_rendered = view.count("\n")
    ```
  - **Fix (alternative):** document the requirement explicitly in the
    `Model.view()` docstring with a concrete example.
  - Files: `renderer.py` (`_flush`), `model.py` (docstring)

- [ ] **Program: send `WindowSizeMsg` at startup, not only on `SIGWINCH`**
  - `WindowSizeMsg` is only emitted from the `SIGWINCH` signal handler. It is
    never sent when the program first starts. Any model that initialises
    `_term_w`/`_term_h` to a default (e.g. 80×24) will use those values for
    the entire session unless the user physically resizes the terminal.
  - For layout-sensitive apps this means the first render uses wrong dimensions,
    which can trigger the line-wrap/line-count cascade described in the items
    above, breaking the display from the very first keypress.
  - This matches a gap vs. the Go port, which always delivers `WindowSizeMsg`
    as the first message the model receives.
  - **Fix:** after `_setup_terminal()` completes, enqueue an initial size
    message before entering the event loop:
    ```python
    try:
        sz = os.get_terminal_size()
        self._msg_queue.put(WindowSizeMsg(sz.columns, sz.lines))
    except OSError:
        pass
    ```
  - Files: `tea.py` (`run`)

- [ ] **Add Python example: multi-field form with text input and navigation**
  - All existing Python examples demonstrate timer/progress/selection patterns
    with low-frequency updates. There are no examples of:
    - Inline text editing with a visible cursor
    - Multiple input fields with Tab/Shift-Tab focus navigation
    - Mixed field types (text, select/cycle, button)
    - Submitting a form and displaying a result
  - Go examples exist (`textinput`, `textinputs`, `credit-card-form`) but are
    not directly portable due to the `bubbles` component library.
  - **Deliverable:** `examples/form.py` — a minimal username + password form
    with tab navigation, inline cursor editing, and a submit button that
    displays the collected values. No external dependencies beyond bubbletea.
  - Files: `examples/form.py` (new)

- [ ] **Clarify `quit_cmd` naming to prevent misuse**
  - `tea.quit_cmd` is a **function** (`def quit_cmd() -> Msg`). Correct usage
    is `return model, tea.quit_cmd` — passing the reference as a Cmd, not
    calling it.
  - The name reads like a pre-made command value, which invites the mistake
    `return model, tea.quit_cmd()` — passing `QuitMsg()` directly as the Cmd.
    `_execute_cmd_async` then tries to call `QuitMsg()` as a function and
    raises `TypeError`.
  - Go uses `tea.Quit` (a plain `Cmd` value). Consider either:
    - Renaming to `tea.quit` with a `tea.quit_cmd` alias + deprecation warning
    - Or adding a `tea.Quit = quit_cmd` alias to match Go naming
  - Files: `commands.py`, `tea.py` (re-export), `__init__.py`
