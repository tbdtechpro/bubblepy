"""
Bubble Tea - A Python TUI framework based on The Elm Architecture.

Ported from the Go library: https://github.com/charmbracelet/bubbletea
"""

from .model import Model
from .tea import Program
from .messages import (
    Msg,
    KeyMsg,
    MouseMsg,
    WindowSizeMsg,
    FocusMsg,
    BlurMsg,
    QuitMsg,
    ClearScreenMsg,
    SetWindowTitleMsg,
    SuspendMsg,
    ResumeMsg,
)
from .keys import Key, KeyType
from .mouse import MouseButton, MouseAction, MouseEvent
from .commands import (
    Cmd,
    BatchMsg,
    SequenceMsg,
    quit_cmd,
    batch,
    sequence,
    set_window_title,
    clear_screen,
    tick,
    every,
)
from .screen import (
    enter_alt_screen,
    exit_alt_screen,
    enable_mouse_cell_motion,
    enable_mouse_all_motion,
    disable_mouse,
    show_cursor,
    hide_cursor,
    suspend,
)

__all__ = [
    # Core
    "Model",
    "Program",
    # Messages
    "Msg",
    "KeyMsg",
    "MouseMsg",
    "WindowSizeMsg",
    "FocusMsg",
    "BlurMsg",
    "QuitMsg",
    "ClearScreenMsg",
    "SetWindowTitleMsg",
    "SuspendMsg",
    "ResumeMsg",
    # Keys
    "Key",
    "KeyType",
    # Mouse
    "MouseButton",
    "MouseAction",
    "MouseEvent",
    # Commands
    "Cmd",
    "BatchMsg",
    "SequenceMsg",
    "quit_cmd",
    "batch",
    "sequence",
    "set_window_title",
    "clear_screen",
    "tick",
    "every",
    # Screen
    "enter_alt_screen",
    "exit_alt_screen",
    "enable_mouse_cell_motion",
    "enable_mouse_all_motion",
    "disable_mouse",
    "show_cursor",
    "hide_cursor",
    "suspend",
    # Version
    "__version__",
]

__version__ = "0.1.0"
