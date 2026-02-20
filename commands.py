"""Commands for Bubble Tea."""

import os
import time
from dataclasses import dataclass
from typing import Callable, Optional

from .messages import ClearScreenMsg, Msg, QuitMsg, SetWindowTitleMsg, WindowSizeMsg

# A Cmd is a callable that returns an optional Msg.
Cmd = Callable[[], Optional[Msg]]


@dataclass
class BatchMsg(Msg):
    """Message carrying commands to be executed concurrently.

    Returned by batch(). The program launches each command in its own
    thread and delivers every resulting message independently to update().
    """

    cmds: list[Cmd]


@dataclass
class SequenceMsg(Msg):
    """Message carrying commands to be executed sequentially.

    Returned by sequence(). The program runs each command in order,
    delivering each resulting message to update() before starting the next.
    """

    cmds: list[Cmd]


def quit_cmd() -> Msg:
    """Command to quit the program.

    Usage:
        return model, quit_cmd
    """
    return QuitMsg()


def batch(*cmds: Optional[Cmd]) -> Optional[Cmd]:
    """Combine multiple commands into one that runs them concurrently.

    Each command runs in its own thread. All resulting messages are
    delivered to update() independently, with no ordering guarantees.
    None commands are silently ignored.

    If no valid commands are provided, returns None.
    If exactly one valid command is provided, returns it directly.

    Args:
        *cmds: Commands to run concurrently.

    Returns:
        A single command whose message triggers concurrent execution,
        or None if there are no valid commands.
    """
    valid_cmds = [c for c in cmds if c is not None]

    if not valid_cmds:
        return None

    if len(valid_cmds) == 1:
        return valid_cmds[0]

    def batched() -> Msg:
        return BatchMsg(cmds=valid_cmds)

    return batched


def sequence(*cmds: Optional[Cmd]) -> Optional[Cmd]:
    """Run commands one at a time, in order.

    Each command runs to completion and its message is delivered to
    update() before the next command starts. Contrast with batch(),
    which runs all commands concurrently.

    None commands are silently skipped. If a command returns None, the
    next command starts immediately without an update() call.

    If no valid commands are provided, returns None.
    If exactly one valid command is provided, returns it directly.

    Args:
        *cmds: Commands to run sequentially.

    Returns:
        A single command whose message triggers sequential execution,
        or None if there are no valid commands.
    """
    valid_cmds = [c for c in cmds if c is not None]

    if not valid_cmds:
        return None

    if len(valid_cmds) == 1:
        return valid_cmds[0]

    def sequenced() -> Msg:
        return SequenceMsg(cmds=valid_cmds)

    return sequenced


def set_window_title(title: str) -> Cmd:
    """Command to set the terminal window title.

    Args:
        title: The window title to display.

    Returns:
        A command that sets the window title.
    """

    def cmd() -> Msg:
        return SetWindowTitleMsg(title=title)

    return cmd


def clear_screen() -> Cmd:
    """Command to clear the terminal screen.

    Returns:
        A command that clears the screen.
    """

    def cmd() -> Msg:
        return ClearScreenMsg()

    return cmd


def tick(duration_seconds: float, fn: Callable[[], Msg]) -> Cmd:
    """Command that sends a message after a one-time delay.

    Args:
        duration_seconds: How long to wait before sending the message.
        fn: Called after the delay to produce the message.

    Returns:
        A command that waits, then returns fn().
    """

    def cmd() -> Optional[Msg]:
        time.sleep(duration_seconds)
        return fn()

    return cmd


def window_size() -> Cmd:
    """Command that queries the current terminal dimensions.

    Returns a WindowSizeMsg with the current width and height so the model
    can size itself at startup without waiting for a SIGWINCH event.
    Returns None if the terminal size cannot be determined (e.g. in a pipe).

    Equivalent to Go's tea.WindowSize() command.

    Example::

        def init(self):
            return tea.window_size()  # get size immediately on start
    """

    def cmd() -> Optional[Msg]:
        try:
            size = os.get_terminal_size()
            return WindowSizeMsg(width=size.columns, height=size.lines)
        except OSError:
            return None

    return cmd


def every(interval_seconds: float, fn: Callable[[], Msg]) -> Cmd:
    """Command that fires once after an interval, delivering fn() to update().

    Following the Elm Architecture pattern, every() fires once per call.
    To keep receiving ticks, return every() again from update() each time
    a tick message is received:

        def update(self, msg):
            if isinstance(msg, TickMsg):
                return self, every(1.0, lambda: TickMsg())
            return self, None

        def init(self):
            return every(1.0, lambda: TickMsg())

    Args:
        interval_seconds: How long to wait before firing.
        fn: Called after the interval to produce the message.

    Returns:
        A command that waits for the interval, then returns fn().
    """

    def cmd() -> Optional[Msg]:
        time.sleep(interval_seconds)
        return fn()

    return cmd
