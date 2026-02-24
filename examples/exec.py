#!/usr/bin/env python3
"""Launch an external editor from a Bubble Tea TUI.

Port of examples/exec/main.go.

Demonstrates exec_process(): the TUI suspends, the editor takes over the
terminal, and the TUI resumes when the editor exits.  Press 'a' to toggle
alt-screen, 'e' to open $EDITOR (defaults to vim), 'q' / ctrl+c to quit.

Run:
    python examples/exec.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dataclasses import dataclass
from typing import Optional

import bubbletea as tea


@dataclass
class EditorFinishedMsg(tea.Msg):
    """Delivered when the external editor exits."""

    err: Optional[Exception]


def open_editor() -> tea.Cmd:
    """Return a Cmd that opens $EDITOR (falling back to vim)."""
    editor = os.environ.get("EDITOR", "vim")
    exec_cmd = tea.ExecCmd([editor])

    def on_done(err: Optional[Exception]) -> Optional[tea.Msg]:
        return EditorFinishedMsg(err=err)

    return tea.exec_process(exec_cmd, on_done)


class EditorModel(tea.Model):
    def __init__(self) -> None:
        self.altscreen_active = False
        self.err: Optional[Exception] = None

    def init(self) -> Optional[tea.Cmd]:
        return None

    def update(self, msg: tea.Msg):
        if isinstance(msg, tea.KeyMsg):
            if msg.key in ("ctrl+c", "q"):
                return self, tea.quit_cmd

            if msg.key == "a":
                self.altscreen_active = not self.altscreen_active
                cmd = tea.enter_alt_screen() if self.altscreen_active else tea.exit_alt_screen()
                return self, cmd

            if msg.key == "e":
                return self, open_editor()

        if isinstance(msg, EditorFinishedMsg):
            if msg.err is not None:
                self.err = msg.err
                return self, tea.quit_cmd

        return self, None

    def view(self) -> str:
        if self.err is not None:
            return f"Error: {self.err}\n"
        return (
            "Press 'e' to open your $EDITOR.\n"
            "Press 'a' to toggle the alt-screen.\n"
            "Press 'q' to quit.\n"
        )


if __name__ == "__main__":
    log_path = os.environ.get("BUBBLETEA_LOG", "")
    if log_path:
        tea.log_to_file(log_path, "exec")

    p = tea.Program(EditorModel())
    try:
        p.run()
    except tea.ErrInterrupted:
        pass
