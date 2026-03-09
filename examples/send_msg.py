#!/usr/bin/env python3
"""Send messages to a running Bubble Tea program from outside.

Port of examples/send-msg/main.go.

Demonstrates using Program.send() from a background thread and
Program.println() to log results above the TUI.

Run:
    python examples/send_msg.py
"""

import os
import random
import sys
import threading
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dataclasses import dataclass
from typing import Optional

import bubblepy as tea

FOODS = [
    "an apple",
    "a pear",
    "a gherkin",
    "a party gherkin",
    "a kohlrabi",
    "some spaghetti",
    "tacos",
    "a currywurst",
    "some curry",
    "a sandwich",
    "some peanut butter",
    "some cashews",
    "some ramen",
]

SPINNER_FRAMES = ["|", "/", "-", "\\"]


@dataclass
class ResultMsg:
    food: str
    duration_ms: int


@dataclass
class SpinnerTickMsg:
    pass


class SendMsgModel(tea.Model):
    MAX_RESULTS = 5

    def __init__(self) -> None:
        self.results: list[ResultMsg] = []
        self.spinner_frame = 0
        self.quitting = False

    def init(self) -> Optional[tea.Cmd]:
        return tea.tick(0.1, SpinnerTickMsg)

    def update(self, msg: tea.Msg):
        if isinstance(msg, tea.KeyMsg):
            self.quitting = True
            return self, tea.quit_cmd

        if isinstance(msg, ResultMsg):
            self.results = (self.results + [msg])[-self.MAX_RESULTS :]
            return self, None

        if isinstance(msg, SpinnerTickMsg):
            self.spinner_frame = (self.spinner_frame + 1) % len(SPINNER_FRAMES)
            return self, tea.tick(0.1, SpinnerTickMsg)

        return self, None

    def view(self) -> str:
        if self.quitting:
            return "That's all for today!\n"

        spinner = SPINNER_FRAMES[self.spinner_frame]
        lines = [f"{spinner} Eating food...\n\n"]

        for r in self.results:
            lines.append(f"  Ate {r.food} ({r.duration_ms}ms)\n")

        while len(lines) < self.MAX_RESULTS + 2:
            lines.append("  ...\n")

        lines.append("\nPress any key to exit.\n")
        return "".join(lines)


def background_eater(p: tea.Program) -> None:
    while True:
        delay = random.randint(100, 999)
        time.sleep(delay / 1000)
        food = random.choice(FOODS)
        try:
            p.send(ResultMsg(food=food, duration_ms=delay))
        except Exception:
            break


if __name__ == "__main__":
    model = SendMsgModel()
    p = tea.Program(model)

    t = threading.Thread(target=background_eater, args=(p,), daemon=True)
    t.start()

    try:
        p.run()
    except tea.ErrInterrupted:
        pass
