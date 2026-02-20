"""External process execution for Bubble Tea.

Provides exec_process(), which temporarily suspends the TUI, runs a
subprocess with full terminal access, then resumes the TUI and delivers
the result via a callback message.

Equivalent to Go's exec.go / tea.ExecProcess().
"""

from dataclasses import dataclass, field
from typing import Callable, Optional, Sequence

from .commands import Cmd
from .messages import Msg


@dataclass
class ExecCmd:
    """Specification for an external command run via exec_process().

    Wraps the arguments passed to subprocess.run().  Additional keyword
    arguments for subprocess.run() (e.g. env, cwd) may be supplied via
    the popen_kwargs dict.

    Analogous to Go's ExecCmd interface.

    Example::

        cmd = tea.ExecCmd(["vim", "notes.txt"])
        return model, tea.exec_process(cmd, on_editor_exit)
    """

    args: Sequence[str]
    popen_kwargs: dict = field(default_factory=dict)


@dataclass
class ExecMsg(Msg):
    """Internal message that triggers external process execution.

    Produced by exec_process() and consumed by the event loop — do not
    create or match against this type in model code.
    """

    exec_cmd: ExecCmd
    callback: Optional[Callable[[Optional[Exception]], Optional[Msg]]]


def exec_process(
    exec_cmd: ExecCmd,
    callback: Optional[Callable[[Optional[Exception]], Optional[Msg]]] = None,
) -> Cmd:
    """Command that suspends the TUI, runs an external process, then resumes.

    The TUI is paused (terminal restored to cooked mode) before the
    subprocess starts so it has full, uncontested terminal access.  After
    the subprocess exits the TUI is resumed and ``callback`` is called with
    the exception (or ``None`` on success) to produce a message that is
    delivered to ``model.update()``.

    Not supported on Windows (silently ignored there).

    Args:
        exec_cmd: The command specification (args + optional subprocess kwargs).
        callback: Called with ``None`` on success or an ``Exception`` on
            non-zero exit / OS error; its return value is sent to update().

    Returns:
        A Cmd that produces ExecMsg for the event loop to handle.

    Equivalent to Go's ``tea.ExecProcess(cmd, fn)``.

    Example::

        def on_done(err):
            return EditorClosedMsg(error=err)

        return model, tea.exec_process(
            tea.ExecCmd(["vim", filename]),
            on_done,
        )
    """

    def cmd() -> Msg:
        return ExecMsg(exec_cmd=exec_cmd, callback=callback)

    return cmd
