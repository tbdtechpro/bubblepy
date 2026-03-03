"""
Bubble Tea - A Python TUI framework based on The Elm Architecture.

Ported from the Go library: https://github.com/charmbracelet/bubbletea
"""

from .commands import (
    BatchMsg,
    Cmd,
    SequenceMsg,
    batch,
    clear_screen,
    every,
    quit_cmd,
    sequence,
    set_window_title,
    tick,
    window_size,
)
from .exec import ExecCmd, exec_process
from .keys import Key, KeyType
from .log import log_to_file
from .messages import (
    BlurMsg,
    ClearScreenMsg,
    CustomMsg,
    FocusMsg,
    InterruptMsg,
    KeyMsg,
    MouseMsg,
    Msg,
    PasteEndMsg,
    PasteMsg,
    PasteStartMsg,
    QuitMsg,
    ResumeMsg,
    SetWindowTitleMsg,
    SuspendMsg,
    WindowSizeMsg,
)
from .model import Model
from .mouse import MouseAction, MouseButton, MouseEvent
from .screen import (
    disable_mouse,
    enable_mouse_all_motion,
    enable_mouse_cell_motion,
    enter_alt_screen,
    exit_alt_screen,
    hide_cursor,
    show_cursor,
    suspend,
)
from .tea import ErrInterrupted, ErrProgramKilled, ErrProgramPanic, Program

__all__ = [
    # Core
    "Model",
    "Program",
    # Messages
    "Msg",
    "CustomMsg",
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
