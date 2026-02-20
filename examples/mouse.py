#!/usr/bin/env python3
"""Display mouse events as they come in.

Port of examples/mouse/main.go.

Run:
    python examples/mouse.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from dataclasses import dataclass, field
from typing import Optional

import bubbletea as tea


MAX_EVENTS = 20


@dataclass
class MouseModel(tea.Model):
    events: list[str] = field(default_factory=list)

    def init(self) -> Optional[tea.Cmd]:
        return None

    def update(self, msg: tea.Msg):
        if isinstance(msg, tea.KeyMsg):
            if msg.key in ("ctrl+c", "q"):
                return self, tea.quit_cmd

        if isinstance(msg, tea.MouseMsg):
            mods = []
            if msg.alt:
                mods.append("alt")
            if msg.ctrl:
                mods.append("ctrl")
            if msg.shift:
                mods.append("shift")
            mod_str = "+".join(mods) + "+" if mods else ""
            entry = (
                f"{mod_str}{msg.action} button={msg.button} "
                f"x={msg.x} y={msg.y}"
            )
            self.events = (self.events + [entry])[-MAX_EVENTS:]

        return self, None

    def view(self) -> str:
        lines = ["Mouse event log (q to quit)\n\n"]
        for ev in self.events:
            lines.append(f"  {ev}\n")
        return "".join(lines)


if __name__ == "__main__":
    p = tea.Program(MouseModel(), mouse_all_motion=True)
    try:
        p.run()
    except tea.ErrInterrupted:
        pass
