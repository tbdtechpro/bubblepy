"""Message types for Bubble Tea."""

from dataclasses import dataclass
from typing import Any, Union


class Msg:
    """Base class for all messages."""
    pass


@dataclass
class KeyMsg(Msg):
    """Message sent when a key is pressed."""
    key: str  # The key string (e.g., "a", "enter", "ctrl+c")
    alt: bool = False  # Whether Alt was held
    
    def __str__(self) -> str:
        if self.alt:
            return f"alt+{self.key}"
        return self.key


@dataclass
class MouseMsg(Msg):
    """Message sent on mouse events."""
    x: int
    y: int
    button: int
    action: str  # "press", "release", "motion", "wheel"
    alt: bool = False
    ctrl: bool = False
    shift: bool = False


@dataclass  
class WindowSizeMsg(Msg):
    """Message sent when the terminal window is resized."""
    width: int
    height: int


@dataclass
class FocusMsg(Msg):
    """Message sent when the terminal gains focus."""
    pass


@dataclass
class BlurMsg(Msg):
    """Message sent when the terminal loses focus."""
    pass


@dataclass
class QuitMsg(Msg):
    """Internal message to signal program quit."""
    pass


@dataclass
class InterruptMsg(Msg):
    """Message sent when the program receives SIGINT (ctrl+c).

    Unlike QuitMsg, InterruptMsg is delivered to the model's update() method
    before the program exits, giving it a chance to react (e.g. save state).
    The event loop then breaks and run() raises ErrInterrupted.
    """
    pass


@dataclass
class CustomMsg(Msg):
    """Wrapper for custom user-defined messages."""
    value: Any


@dataclass
class SuspendMsg(Msg):
    """Message that suspends the program (e.g. ctrl+z / SIGTSTP).

    The event loop handles this by restoring the terminal, sending SIGTSTP
    to the process, and emitting ResumeMsg when SIGCONT is received.
    Models may react to SuspendMsg to save state before suspension.
    """
    pass


@dataclass
class ResumeMsg(Msg):
    """Message delivered to the model after the program resumes from suspension."""
    pass


@dataclass
class ClearScreenMsg(Msg):
    """Message that instructs the renderer to clear the terminal screen."""
    pass


@dataclass
class SetWindowTitleMsg(Msg):
    """Message that sets the terminal window title."""
    title: str
