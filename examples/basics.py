#!/usr/bin/env python3
"""
Basic Bubble Tea example - Shopping List.

This is a port of the Go tutorial example.
"""

import sys
from typing import Dict, Optional, Tuple

# Add parent directory to path for development
sys.path.insert(0, str(__file__).rsplit("/", 2)[0])

import bubbletea as tea


class ShoppingListModel(tea.Model):
    """Model for the shopping list application."""

    def __init__(
        self,
        choices: list[str],
        cursor: int = 0,
        selected: Optional[Dict[int, bool]] = None,
    ):
        self.choices = choices
        self.cursor = cursor
        self.selected = selected or {}

    def init(self) -> Optional[tea.Cmd]:
        """No initial command needed."""
        return None

    def update(self, msg: tea.Msg) -> Tuple["ShoppingListModel", Optional[tea.Cmd]]:
        """Handle incoming messages."""

        if isinstance(msg, tea.KeyMsg):
            key = msg.key

            # Quit keys
            if key in ("ctrl+c", "q"):
                return self, tea.quit_cmd

            # Navigation
            if key in ("up", "k"):
                if self.cursor > 0:
                    self.cursor -= 1

            elif key in ("down", "j"):
                if self.cursor < len(self.choices) - 1:
                    self.cursor += 1

            # Toggle selection
            elif key in ("enter", " "):
                if self.cursor in self.selected:
                    del self.selected[self.cursor]
                else:
                    self.selected[self.cursor] = True

        return self, None

    def view(self) -> str:
        """Render the UI."""
        # Header
        s = "What should we buy at the market?\n\n"

        # Choices
        for i, choice in enumerate(self.choices):
            # Cursor
            cursor = ">" if i == self.cursor else " "

            # Checkbox
            checked = "x" if i in self.selected else " "

            # Row
            s += f"{cursor} [{checked}] {choice}\n"

        # Footer
        s += "\nPress q to quit.\n"

        return s


def initial_model() -> ShoppingListModel:
    """Create the initial model."""
    return ShoppingListModel(
        choices=[
            "Buy carrots",
            "Buy celery",
            "Buy kohlrabi",
        ]
    )


def main():
    """Run the program."""
    p = tea.Program(initial_model())

    try:
        final_model = p.run()

        # Show what was selected
        if isinstance(final_model, ShoppingListModel) and final_model.selected:
            print("\nYou selected:")
            for i, choice in enumerate(final_model.choices):
                if i in final_model.selected:
                    print(f"  - {choice}")
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
