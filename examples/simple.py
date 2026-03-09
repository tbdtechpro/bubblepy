#!/usr/bin/env python3
"""A simple program that counts down from 5 and then exits.

Port of examples/simple/main.go.

Run:
    python examples/simple.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dataclasses import dataclass
from typing import Optional

import bubblepy as tea


@dataclass
class TickMsg:
    """Sent every second to advance the countdown."""

    pass


class CountdownModel(tea.Model):
    def __init__(self, seconds: int = 5) -> None:
        self.seconds = seconds

    def init(self) -> Optional[tea.Cmd]:
        return tea.tick(1.0, TickMsg)

    def update(self, msg: tea.Msg):
        if isinstance(msg, tea.KeyMsg):
            if msg.key in ("ctrl+c", "q"):
                return self, tea.quit_cmd
            if msg.key == "ctrl+z":
                return self, tea.suspend()

        if isinstance(msg, TickMsg):
            self.seconds -= 1
            if self.seconds <= 0:
                return self, tea.quit_cmd
            return self, tea.tick(1.0, TickMsg)

        return self, None

    def view(self) -> str:
        return (
            f"Hi. This program will exit in {self.seconds} seconds.\n\n"
            "To quit sooner press ctrl-c, or press ctrl-z to suspend...\n"
        )


if __name__ == "__main__":
    log_path = os.environ.get("BUBBLETEA_LOG", "")
    if log_path:
        tea.log_to_file(log_path, "simple")

    p = tea.Program(CountdownModel(5))
    try:
        p.run()
    except tea.ErrInterrupted:
        pass
