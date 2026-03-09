#!/usr/bin/env python3
"""An example demonstrating an application with multiple views.

Port of examples/views/main.go.

The first view lets you pick a task from a list.  After choosing, a
second view simulates a progress bar loading, then exits automatically.

Run:
    python examples/views.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dataclasses import dataclass
from typing import Optional

import bubblepy as tea

CHOICES = [
    "Plant carrots",
    "Go to the market",
    "Read something",
    "See friends",
]

PROGRESS_WIDTH = 40


@dataclass
class TickMsg:
    pass


@dataclass
class FrameMsg:
    pass


@dataclass
class ViewsModel(tea.Model):
    choice: int = 0
    chosen: bool = False
    ticks: int = 10
    frames: int = 0
    progress: float = 0.0
    loaded: bool = False
    quitting: bool = False

    def init(self) -> Optional[tea.Cmd]:
        return tea.tick(1.0, TickMsg)

    def update(self, msg: tea.Msg):
        # Global quit keys
        if isinstance(msg, tea.KeyMsg):
            if msg.key in ("q", "escape", "ctrl+c"):
                self.quitting = True
                return self, tea.quit_cmd

        if not self.chosen:
            return self._update_choices(msg)
        return self._update_chosen(msg)

    def _update_choices(self, msg: tea.Msg):
        if isinstance(msg, tea.KeyMsg):
            if msg.key in ("j", "down"):
                self.choice = min(self.choice + 1, len(CHOICES) - 1)
            elif msg.key in ("k", "up"):
                self.choice = max(self.choice - 1, 0)
            elif msg.key == "enter":
                self.chosen = True
                return self, tea.tick(1 / 60, FrameMsg)

        if isinstance(msg, TickMsg):
            if self.ticks == 0:
                self.quitting = True
                return self, tea.quit_cmd
            self.ticks -= 1
            return self, tea.tick(1.0, TickMsg)

        return self, None

    def _update_chosen(self, msg: tea.Msg):
        if isinstance(msg, FrameMsg):
            if not self.loaded:
                self.frames += 1
                self.progress = min(self.frames / 100, 1.0)
                if self.progress >= 1.0:
                    self.loaded = True
                    self.ticks = 3
                    return self, tea.tick(1.0, TickMsg)
                return self, tea.tick(1 / 60, FrameMsg)

        if isinstance(msg, TickMsg) and self.loaded:
            if self.ticks == 0:
                self.quitting = True
                return self, tea.quit_cmd
            self.ticks -= 1
            return self, tea.tick(1.0, TickMsg)

        return self, None

    def view(self) -> str:
        if self.quitting:
            return "\n  See you later!\n\n"
        if not self.chosen:
            return self._choices_view()
        return self._chosen_view()

    def _choices_view(self) -> str:
        lines = ["  What to do today?\n\n"]
        for i, c in enumerate(CHOICES):
            marker = "[x]" if i == self.choice else "[ ]"
            lines.append(f"  {marker} {c}\n")
        lines.append(f"\n  Program quits in {self.ticks}s\n\n")
        lines.append("  j/k: select  •  enter: choose  •  q: quit\n")
        return "".join(lines)

    def _chosen_view(self) -> str:
        msgs = [
            "Carrot planting?\n\n  We'll need libgarden and vegeutils...",
            "A trip to the market?\n\n  Install marketkit and libshopping...",
            "Reading time?\n\n  We'll need an actual library.",
            "It's always good to see friends.\n\n  Fetching social-skills...",
        ]
        body = msgs[self.choice]

        filled = int(PROGRESS_WIDTH * self.progress)
        bar = "█" * filled + "░" * (PROGRESS_WIDTH - filled)
        pct = int(self.progress * 100)

        if self.loaded:
            label = f"Done! Exiting in {self.ticks}s..."
        else:
            label = "Downloading..."

        return f"\n  {body}\n\n  {label}\n  [{bar}] {pct}%\n"


if __name__ == "__main__":
    p = tea.Program(ViewsModel())
    try:
        p.run()
    except tea.ErrInterrupted:
        pass
