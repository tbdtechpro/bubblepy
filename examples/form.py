#!/usr/bin/env python3
"""
Multi-field form example for Bubble Tea (Python port).

Demonstrates:
  - Inline text editing with a visible cursor
  - Tab / Shift-Tab focus navigation between fields
  - A submit button
  - Displaying collected values after submission

Run:
    python examples/form.py
"""

import sys
from typing import Optional, Tuple

sys.path.insert(0, str(__file__).rsplit("/", 2)[0])

import bubblepy as tea

# ── Field indices ────────────────────────────────────────────────────────────

FIELD_USERNAME = 0
FIELD_PASSWORD = 1
FIELD_SUBMIT = 2
NUM_FIELDS = 3

# ── Model ────────────────────────────────────────────────────────────────────


class FormModel(tea.Model):
    """A minimal username/password form with tab navigation."""

    def __init__(self) -> None:
        self.username: str = ""
        self.password: str = ""
        self.focus: int = FIELD_USERNAME
        self.submitted: bool = False
        self.width: int = 80

    def init(self) -> Optional[tea.Cmd]:
        return tea.window_size()

    def update(self, msg: tea.Msg) -> Tuple["FormModel", Optional[tea.Cmd]]:
        if isinstance(msg, tea.WindowSizeMsg):
            self.width = msg.width
            return self, None

        if isinstance(msg, tea.KeyMsg):
            return self._handle_key(msg.key)

        return self, None

    def _handle_key(self, key: str) -> Tuple["FormModel", Optional[tea.Cmd]]:
        if key == "ctrl+c":
            return self, tea.Quit

        if self.submitted:
            if key == "q":
                return self, tea.Quit
            return self, None

        if key == "tab":
            self.focus = (self.focus + 1) % NUM_FIELDS
            return self, None
        if key == "shift+tab":
            self.focus = (self.focus - 1) % NUM_FIELDS
            return self, None

        if key == "enter":
            if self.focus == FIELD_SUBMIT:
                self.submitted = True
            else:
                self.focus = (self.focus + 1) % NUM_FIELDS
            return self, None

        if self.focus == FIELD_USERNAME:
            self.username = _edit(self.username, key)
        elif self.focus == FIELD_PASSWORD:
            self.password = _edit(self.password, key)

        return self, None

    def view(self) -> str:
        if self.submitted:
            return _submitted_view(self.username, self.password)
        return _form_view(self)


# ── View helpers ─────────────────────────────────────────────────────────────


def _edit(text: str, key: str) -> str:
    """Apply a single keypress to a text buffer."""
    if key in ("backspace", "ctrl+h") and text:
        return text[:-1]
    if len(key) == 1 and key.isprintable():
        return text + key
    return text


def _field(label: str, value: str, focused: bool, obscure: bool = False) -> str:
    display = "*" * len(value) if obscure else value
    cursor = "_" if focused else " "
    border = ">" if focused else " "
    return f"{border} {label}: [{display}{cursor}]"


def _button(label: str, focused: bool) -> str:
    if focused:
        return f"  [ {label} ]  <- Enter to submit"
    return f"  [ {label} ]"


def _form_view(m: "FormModel") -> str:
    lines = [
        "+----- Login ----------------------+",
        "",
        _field("Username", m.username, m.focus == FIELD_USERNAME),
        "",
        _field("Password", m.password, m.focus == FIELD_PASSWORD, obscure=True),
        "",
        _button("Submit", m.focus == FIELD_SUBMIT),
        "",
        "+----------------------------------+",
        "",
        "  Tab / Shift-Tab to move  Enter to confirm  Ctrl+C to quit",
        "",
    ]
    return "\n".join(lines) + "\n"


def _submitted_view(username: str, password: str) -> str:
    lines = [
        "",
        "  Form submitted!",
        "",
        f"  Username : {username}",
        f"  Password : {'*' * len(password)}",
        "",
        "  Press q or Ctrl+C to exit.",
        "",
    ]
    return "\n".join(lines) + "\n"


# ── Entry point ──────────────────────────────────────────────────────────────


def main() -> None:
    p = tea.Program(FormModel())
    try:
        p.run()
    except (tea.ErrInterrupted, tea.ErrProgramKilled):
        pass


if __name__ == "__main__":
    main()
