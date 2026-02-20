"""Screen control sequences for Bubble Tea."""

import sys
from dataclasses import dataclass
from typing import Optional
from .messages import Msg, SuspendMsg
from .commands import Cmd


# ANSI escape sequences
ESC = "\x1b"
CSI = f"{ESC}["

# Screen control
ALT_SCREEN_ON = f"{CSI}?1049h"
ALT_SCREEN_OFF = f"{CSI}?1049l"

# Cursor control
CURSOR_HIDE = f"{CSI}?25l"
CURSOR_SHOW = f"{CSI}?25h"
CURSOR_HOME = f"{CSI}H"
CURSOR_SAVE = f"{ESC}7"
CURSOR_RESTORE = f"{ESC}8"

# Clear screen
CLEAR_SCREEN = f"{CSI}2J"
CLEAR_LINE = f"{CSI}2K"
CLEAR_LINE_RIGHT = f"{CSI}K"
CLEAR_LINE_LEFT = f"{CSI}1K"

# Mouse modes
MOUSE_ENABLE = f"{CSI}?1000h"  # Basic mouse reporting
MOUSE_DISABLE = f"{CSI}?1000l"
MOUSE_CELL_MOTION = f"{CSI}?1002h"  # Cell motion tracking
MOUSE_CELL_MOTION_OFF = f"{CSI}?1002l"
MOUSE_ALL_MOTION = f"{CSI}?1003h"  # All motion tracking
MOUSE_ALL_MOTION_OFF = f"{CSI}?1003l"
MOUSE_SGR = f"{CSI}?1006h"  # SGR extended mode
MOUSE_SGR_OFF = f"{CSI}?1006l"

# Focus events
FOCUS_ENABLE = f"{CSI}?1004h"
FOCUS_DISABLE = f"{CSI}?1004l"

# Bracketed paste
BRACKETED_PASTE_ON = f"{CSI}?2004h"
BRACKETED_PASTE_OFF = f"{CSI}?2004l"


# Message types for screen commands
@dataclass
class EnterAltScreenMsg(Msg):
    pass


@dataclass
class ExitAltScreenMsg(Msg):
    pass


@dataclass
class EnableMouseCellMotionMsg(Msg):
    pass


@dataclass
class EnableMouseAllMotionMsg(Msg):
    pass


@dataclass
class DisableMouseMsg(Msg):
    pass


@dataclass
class ShowCursorMsg(Msg):
    pass


@dataclass
class HideCursorMsg(Msg):
    pass


# Command functions
def enter_alt_screen() -> Cmd:
    """Command to enter the alternate screen buffer."""
    def cmd() -> Msg:
        return EnterAltScreenMsg()
    return cmd


def exit_alt_screen() -> Cmd:
    """Command to exit the alternate screen buffer."""
    def cmd() -> Msg:
        return ExitAltScreenMsg()
    return cmd


def enable_mouse_cell_motion() -> Cmd:
    """Command to enable mouse cell motion tracking."""
    def cmd() -> Msg:
        return EnableMouseCellMotionMsg()
    return cmd


def enable_mouse_all_motion() -> Cmd:
    """Command to enable mouse all motion tracking."""
    def cmd() -> Msg:
        return EnableMouseAllMotionMsg()
    return cmd


def disable_mouse() -> Cmd:
    """Command to disable mouse tracking."""
    def cmd() -> Msg:
        return DisableMouseMsg()
    return cmd


def show_cursor() -> Cmd:
    """Command to show the cursor."""
    def cmd() -> Msg:
        return ShowCursorMsg()
    return cmd


def hide_cursor() -> Cmd:
    """Command to hide the cursor."""
    def cmd() -> Msg:
        return HideCursorMsg()
    return cmd


def suspend() -> Cmd:
    """Command to suspend the program (equivalent to ctrl+z / SIGTSTP).

    The event loop handles SuspendMsg by restoring the terminal, sending
    SIGTSTP to the process, and emitting ResumeMsg when SIGCONT is received.
    Not supported on Windows; the message is silently ignored there.
    """
    def cmd() -> Msg:
        return SuspendMsg()
    return cmd


def move_cursor(row: int, col: int) -> str:
    """Return escape sequence to move cursor to position."""
    return f"{CSI}{row};{col}H"


def cursor_up(n: int = 1) -> str:
    """Return escape sequence to move cursor up."""
    return f"{CSI}{n}A"


def cursor_down(n: int = 1) -> str:
    """Return escape sequence to move cursor down."""
    return f"{CSI}{n}B"


def cursor_forward(n: int = 1) -> str:
    """Return escape sequence to move cursor forward."""
    return f"{CSI}{n}C"


def cursor_back(n: int = 1) -> str:
    """Return escape sequence to move cursor back."""
    return f"{CSI}{n}D"
