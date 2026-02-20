"""
Bubble Tea - A Python TUI framework based on The Elm Architecture.

Ported from the Go library: https://github.com/charmbracelet/bubbletea
"""

from .model import Model
from .tea import Program, ErrInterrupted, ErrProgramKilled, ErrProgramPanic
from .messages import (
    Msg,
    KeyMsg,
    MouseMsg,
    WindowSizeMsg,
    FocusMsg,
    BlurMsg,
    QuitMsg,
    InterruptMsg,
    ClearScreenMsg,
    SetWindowTitleMsg,
    SuspendMsg,
    ResumeMsg,
    PasteStartMsg,
    PasteEndMsg,
    PasteMsg,
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
    window_size,
)
from .exec import ExecCmd, exec_process
from .log import log_to_file
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
    "InterruptMsg",
    "ClearScreenMsg",
    "SetWindowTitleMsg",
    "SuspendMsg",
    "ResumeMsg",
    "PasteStartMsg",
    "PasteEndMsg",
    "PasteMsg",
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
    "window_size",
    # Exec
    "ExecCmd",
    "exec_process",
    # Logging
    "log_to_file",
    # Screen
    "enter_alt_screen",
    "exit_alt_screen",
    "enable_mouse_cell_motion",
    "enable_mouse_all_motion",
    "disable_mouse",
    "show_cursor",
    "hide_cursor",
    "suspend",
    # Exceptions
    "ErrInterrupted",
    "ErrProgramKilled",
    "ErrProgramPanic",
    # Version
    "__version__",
]

__version__ = "0.1.0"
