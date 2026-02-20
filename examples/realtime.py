#!/usr/bin/env python3
"""Real-time updates from an external goroutine (thread in Python).

Port of examples/realtime/main.go.

Demonstrates using Program.send() to push messages into a running TUI
from a background thread.

Run:
    python examples/realtime.py
"""

import os
import random
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dataclasses import dataclass
from typing import Optional

import bubbletea as tea


@dataclass
class ResponseMsg:
    """Represents a response from a simulated background worker."""

    duration_ms: int


class RealtimeModel(tea.Model):
    MAX_RESULTS = 5

    def __init__(self) -> None:
        self.responses: list[ResponseMsg] = []
        self.quitting = False

    def init(self) -> Optional[tea.Cmd]:
        return None

    def update(self, msg: tea.Msg):
        if isinstance(msg, tea.KeyMsg):
            self.quitting = True
            return self, tea.quit_cmd

        if isinstance(msg, ResponseMsg):
            self.responses = (self.responses + [msg])[-self.MAX_RESULTS :]
            return self, None

        return self, None

    def view(self) -> str:
        if self.quitting:
            return "Bye!\n"

        lines = ["Waiting for responses...\n\n"]
        for r in self.responses:
            lines.append(f"  Got response in {r.duration_ms}ms\n")

        # Pad so the view height stays constant
        while len(lines) < self.MAX_RESULTS + 2:
            lines.append("\n")

        lines.append("\nPress any key to quit.\n")
        return "".join(lines)


def background_worker(p: tea.Program) -> None:
    """Simulate a worker that sends results at random intervals."""
    while True:
        delay = random.randint(100, 900)
        time.sleep(delay / 1000)
        try:
            p.send(ResponseMsg(duration_ms=delay))
        except Exception:
            break


if __name__ == "__main__":
    model = RealtimeModel()
    p = tea.Program(model)

    t = threading.Thread(target=background_worker, args=(p,), daemon=True)
    t.start()

    try:
        p.run()
    except tea.ErrInterrupted:
        pass
