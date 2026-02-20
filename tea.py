"""Core Program class for Bubble Tea."""

import os
import sys
import select
import signal
import termios
import tty
from typing import Optional, TextIO, Callable, Any
from queue import Queue, Empty
from threading import Thread, Event

from .model import Model
from .messages import (
    Msg, KeyMsg, MouseMsg, WindowSizeMsg,
    QuitMsg, InterruptMsg, FocusMsg, BlurMsg,
    ClearScreenMsg, SetWindowTitleMsg,
    SuspendMsg, ResumeMsg,
    PasteStartMsg, PasteEndMsg, PasteMsg,
)


# ── Sentinel exceptions returned / raised by Program.run() ──────────────────

class ErrInterrupted(Exception):
    """Raised by Program.run() when the program exits via SIGINT / ctrl+c."""


class ErrProgramKilled(Exception):
    """Raised by Program.run() when the program exits via Program.kill()."""


class ErrProgramPanic(Exception):
    """Raised by Program.run() when the model or a command raises an unhandled exception."""
from .keys import parse_key
from .mouse import parse_mouse_event
from .renderer import Renderer, NullRenderer
from .commands import Cmd, BatchMsg, SequenceMsg
from .screen import (
    EnterAltScreenMsg, ExitAltScreenMsg,
    EnableMouseCellMotionMsg, EnableMouseAllMotionMsg, DisableMouseMsg,
    ShowCursorMsg, HideCursorMsg,
)
from .exec import ExecMsg


class Program:
    """
    A Bubble Tea program.
    
    Creates a new TUI application with the given model.
    """
    
    def __init__(
        self,
        model: Model,
        *,
        input_tty: Optional[TextIO] = None,
        output: Optional[TextIO] = None,
        alt_screen: bool = False,
        mouse_cell_motion: bool = False,
        mouse_all_motion: bool = False,
        bracketed_paste: bool = False,
        fps: int = 60,
        stop_event: Optional[Event] = None,
        filter: Optional[Callable[[Model, Msg], Optional[Msg]]] = None,
        report_focus: bool = False,
        use_null_renderer: bool = False,
    ):
        """Initialize a new Program.

        Args:
            model: The initial model.
            input_tty: Input file (defaults to stdin).
            output: Output file (defaults to stdout).
            alt_screen: Whether to use alternate screen buffer.
            mouse_cell_motion: Enable mouse cell motion tracking.
            mouse_all_motion: Enable mouse all motion tracking.
            bracketed_paste: Enable bracketed paste mode.
            fps: Frames per second for rendering (clamped to [1, 120]).
            stop_event: Optional threading.Event; when set, the program exits
                gracefully as if quit() were called.  Equivalent to Go's
                WithContext(ctx) — pass an Event that you set to cancel.
            filter: Optional callable ``filter(model, msg) -> Optional[Msg]``.
                Invoked for every message before it reaches model.update().
                Return the (possibly transformed) message to continue normal
                processing, or None to discard it.  Equivalent to Go's
                WithFilter option.
            report_focus: When True, enable terminal focus reporting.  The
                input reader emits FocusMsg when the terminal gains focus and
                BlurMsg when it loses focus.  Equivalent to Go's
                WithReportFocus option.
            use_null_renderer: When True, swap the normal renderer for
                NullRenderer (all rendering is a no-op).  Useful for headless
                testing.  Equivalent to Go's WithoutRenderer option.
        """
        self.model = model
        self.input_tty = input_tty or sys.stdin
        self.output = output or sys.stdout
        self._use_alt_screen = alt_screen
        self._mouse_cell_motion = mouse_cell_motion
        self._mouse_all_motion = mouse_all_motion
        self._bracketed_paste = bracketed_paste
        self._stop_event = stop_event
        self._filter = filter
        self._report_focus = report_focus

        self._renderer: Renderer = (
            NullRenderer(self.output, fps) if use_null_renderer
            else Renderer(self.output, fps)
        )
        self._msg_queue: Queue[Msg] = Queue()
        self._quit = Event()
        self._killed = Event()
        self._interrupted = Event()
        self._done = Event()
        self._running = False
        self._old_termios: Optional[list] = None
        self._input_thread: Optional[Thread] = None
        self._panic: Optional[BaseException] = None
    
    def run(self) -> Model:
        """
        Run the program and block until it exits.
        
        Returns:
            The final model state
        """
        self._running = True

        try:
            self._setup_terminal()
            self._renderer.start()  # begin FPS-capped render ticker
            self._setup_signals()

            # Initialize model and queue the initial render.
            try:
                cmd = self.model.init()
            except Exception as exc:
                raise ErrProgramPanic("model.init() raised an exception") from exc
            if cmd is not None:
                self._execute_cmd(cmd)
            self._render()

            # Start input reader thread
            self._start_input_reader()

            # Main event loop — wrapped so the terminal is always restored.
            try:
                self._event_loop()
            except Exception as exc:
                raise ErrProgramPanic("unhandled exception in event loop") from exc

        finally:
            self._cleanup()
            self._done.set()

        # Surface typed exit conditions after terminal is restored.
        if self._panic is not None:
            raise ErrProgramPanic("unhandled exception in command") from self._panic
        if self._killed.is_set():
            raise ErrProgramKilled("program was killed")
        if self._interrupted.is_set():
            raise ErrInterrupted("program was interrupted")

        return self.model
    
    def quit(self) -> None:
        """Signal the program to quit gracefully."""
        self._quit.set()
        self._msg_queue.put(QuitMsg())

    def kill(self) -> None:
        """Terminate the program immediately, bypassing any queued messages.

        Unlike quit(), kill() does not wait for the message queue to drain.
        The event loop exits on its next iteration regardless of what is
        pending in the queue.  Equivalent to Go's Program.Kill().
        """
        self._killed.set()
        self._quit.set()
        self._msg_queue.put(QuitMsg())  # unblock queue.get()

    def wait(self) -> None:
        """Block until the program has fully exited and the terminal is restored.

        Useful when driving the program from a separate thread: call kill()
        or quit() from that thread, then wait() to ensure cleanup is complete
        before accessing the terminal again.  Equivalent to Go's Program.Wait().
        """
        self._done.wait()

    def send(self, msg: Msg) -> None:
        """Send a message to the program."""
        self._msg_queue.put(msg)

    def set_window_title(self, title: str) -> None:
        """Set the terminal window title from outside the model.

        Enqueues a SetWindowTitleMsg so the renderer handles it on the next
        event-loop iteration.  Equivalent to Go's Program.SetWindowTitle().
        """
        self._msg_queue.put(SetWindowTitleMsg(title=title))

    def println(self, *args: object) -> None:
        """Print a line above the TUI, persisting across re-renders.

        Joins args with spaces, exactly like Python's built-in print().
        The line scrolls into the terminal's scrollback buffer and is never
        erased by subsequent TUI updates.  A no-op in alt-screen mode.
        Equivalent to Go's Program.Println().
        """
        self._renderer.print_line(" ".join(str(a) for a in args))

    def printf(self, fmt_str: str, *args: object) -> None:
        """Print a formatted line above the TUI, persisting across re-renders.

        Formats the string with % formatting when args are provided,
        otherwise uses fmt_str as-is.  Equivalent to Go's Program.Printf().
        """
        self._renderer.print_line(fmt_str % args if args else fmt_str)
    
    def _event_loop(self) -> None:
        """Main event loop."""
        while not self._quit.is_set():
            # Context cancellation: treat an external stop_event like quit().
            if self._stop_event is not None and self._stop_event.is_set():
                break

            try:
                # Wait for a message
                msg = self._msg_queue.get(timeout=0.1)
            except Empty:
                continue

            # kill() exits immediately, bypassing remaining queued messages.
            if self._killed.is_set():
                break

            # Apply the optional message filter before any further processing,
            # matching Go's WithFilter semantics: the filter sees every message
            # including QuitMsg and InterruptMsg.
            if self._filter is not None:
                msg = self._filter(self.model, msg)
                if msg is None:
                    continue  # message discarded by filter

            # Graceful quit via QuitMsg.
            if isinstance(msg, QuitMsg):
                break

            # ctrl+c / SIGINT: let the model react, then exit.
            if isinstance(msg, InterruptMsg):
                self.model, _ = self.model.update(msg)
                self._render()
                self._interrupted.set()
                break

            # Concurrent command execution — do not pass to update().
            if isinstance(msg, BatchMsg):
                self._execute_batch_cmds(msg.cmds)
                continue

            # Sequential command execution — do not pass to update().
            if isinstance(msg, SequenceMsg):
                self._start_sequence(msg.cmds)
                continue

            # Screen / renderer control messages — do not pass to update().
            if isinstance(msg, EnterAltScreenMsg):
                self._renderer.enter_alt_screen()
                continue
            elif isinstance(msg, ExitAltScreenMsg):
                self._renderer.exit_alt_screen()
                continue
            elif isinstance(msg, EnableMouseCellMotionMsg):
                self._renderer.enable_mouse(all_motion=False)
                continue
            elif isinstance(msg, EnableMouseAllMotionMsg):
                self._renderer.enable_mouse(all_motion=True)
                continue
            elif isinstance(msg, DisableMouseMsg):
                self._renderer.disable_mouse()
                continue
            elif isinstance(msg, ShowCursorMsg):
                self._renderer.show_cursor()
                continue
            elif isinstance(msg, HideCursorMsg):
                self._renderer.hide_cursor()
                continue
            elif isinstance(msg, ClearScreenMsg):
                self._renderer.clear()
                continue
            elif isinstance(msg, SetWindowTitleMsg):
                self._renderer.set_window_title(msg.title)
                continue
            elif isinstance(msg, SuspendMsg):
                self._suspend()
                continue
            elif isinstance(msg, ExecMsg):
                self._handle_exec(msg)
                continue

            # Hand the message to the model.
            self.model, cmd = self.model.update(msg)

            if cmd is not None:
                self._execute_cmd(cmd)

            self._render()
    
    def _render(self) -> None:
        """Render the current view."""
        view = self.model.view()
        self._renderer.render(view)
    
    def _execute_cmd(self, cmd: Cmd) -> None:
        """Execute a command in a background thread.

        The command may return any Msg, including BatchMsg or SequenceMsg,
        which the event loop will dispatch appropriately.
        """
        self._execute_cmd_async(cmd)

    def _execute_cmd_async(self, cmd: Cmd) -> None:
        """Run a single command in a daemon thread and enqueue its result.

        If the command raises an unhandled exception the error is stored in
        self._panic and a QuitMsg is queued so the event loop exits cleanly.
        run() will then re-raise it as ErrProgramPanic after terminal cleanup.
        """
        def run() -> None:
            try:
                result = cmd()
                if result is not None:
                    self._msg_queue.put(result)
            except Exception as exc:
                self._panic = exc
                self._msg_queue.put(QuitMsg())

        thread = Thread(target=run, daemon=True)
        thread.start()

    def _execute_batch_cmds(self, cmds: list) -> None:
        """Launch each command concurrently in its own daemon thread.

        All resulting messages are delivered independently to the event loop;
        there are no ordering guarantees between them.
        """
        for cmd in cmds:
            if cmd is not None:
                self._execute_cmd_async(cmd)

    def _start_sequence(self, cmds: list) -> None:
        """Run commands sequentially in a single daemon thread.

        Each command runs to completion and its message (if any) is placed
        on the queue before the next command starts.  BatchMsg or SequenceMsg
        returned by a step are placed on the queue for the event loop to
        dispatch — nesting is supported.
        """
        def run() -> None:
            for cmd in cmds:
                if cmd is None:
                    continue
                try:
                    msg = cmd()
                except Exception:
                    return
                if msg is not None:
                    self._msg_queue.put(msg)

        thread = Thread(target=run, daemon=True)
        thread.start()
    
    def _setup_terminal(self) -> None:
        """Set up the terminal for raw mode."""
        # Save current terminal settings
        if self.input_tty.isatty():
            fd = self.input_tty.fileno()
            self._old_termios = termios.tcgetattr(fd)
            tty.setraw(fd)
        
        # Enter alt screen if requested
        if self._use_alt_screen:
            self._renderer.enter_alt_screen()
        
        # Enable mouse if requested
        if self._mouse_all_motion:
            self._renderer.enable_mouse(all_motion=True)
        elif self._mouse_cell_motion:
            self._renderer.enable_mouse(all_motion=False)
        
        # Hide cursor
        self._renderer.hide_cursor()
        
        # Bracketed paste
        if self._bracketed_paste:
            self.output.write("\x1b[?2004h")
            self.output.flush()

        # Focus reporting
        if self._report_focus:
            self.output.write("\x1b[?1004h")
            self.output.flush()
    
    def _cleanup(self) -> None:
        """Clean up terminal state."""
        self._quit.set()
        
        # Wait for input thread
        if self._input_thread and self._input_thread.is_alive():
            self._input_thread.join(timeout=0.5)
        
        # Restore terminal
        if self._old_termios is not None and self.input_tty.isatty():
            fd = self.input_tty.fileno()
            termios.tcsetattr(fd, termios.TCSADRAIN, self._old_termios)
        
        # Disable bracketed paste
        if self._bracketed_paste:
            self.output.write("\x1b[?2004l")
            self.output.flush()

        # Disable focus reporting
        if self._report_focus:
            self.output.write("\x1b[?1004l")
            self.output.flush()
        
        # Clean up renderer
        self._renderer.close()
        
        # Print newline for clean exit
        self.output.write("\n")
        self.output.flush()
    
    def _setup_signals(self) -> None:
        """Set up signal handlers."""
        def handle_resize(signum: int, frame: Any) -> None:
            try:
                size = os.get_terminal_size()
                self._msg_queue.put(WindowSizeMsg(size.columns, size.lines))
            except OSError:
                pass

        def handle_int(signum: int, frame: Any) -> None:
            # Send InterruptMsg so the model sees it; the event loop will
            # then break and run() raises ErrInterrupted.
            self._msg_queue.put(InterruptMsg())

        def handle_term(signum: int, frame: Any) -> None:
            self._msg_queue.put(QuitMsg())

        try:
            signal.signal(signal.SIGWINCH, handle_resize)
            signal.signal(signal.SIGINT, handle_int)
            signal.signal(signal.SIGTERM, handle_term)
        except ValueError:
            # signal.signal() only works in the main thread.  When run()
            # is called from a background thread (e.g. in tests) we skip
            # signal setup silently — keyboard interrupts won't be caught
            # but the program will still exit via quit() / kill().
            pass

    def release_terminal(self) -> None:
        """Temporarily restore the terminal to its original cooked mode.

        Stops the renderer, shows the cursor, exits alt-screen, disables
        mouse, and restores the saved termios settings.  Call
        restore_terminal() to reclaim the terminal and resume rendering.

        Useful before launching an external process that needs full terminal
        access (e.g. an editor).  Equivalent to Go's Program.ReleaseTerminal().
        """
        self._renderer.kill()
        self._renderer.show_cursor()
        self._renderer.exit_alt_screen()
        self._renderer.disable_mouse()

        if self._bracketed_paste:
            self.output.write("\x1b[?2004l")
            self.output.flush()

        if self._report_focus:
            self.output.write("\x1b[?1004l")
            self.output.flush()

        if self._old_termios is not None and self.input_tty.isatty():
            termios.tcsetattr(
                self.input_tty.fileno(), termios.TCSADRAIN, self._old_termios
            )

    def restore_terminal(self) -> None:
        """Reclaim the terminal after release_terminal().

        Re-enters raw mode, re-enables all configured terminal features,
        restarts the renderer, and forces a full repaint.
        Equivalent to Go's Program.RestoreTerminal().
        """
        if self.input_tty.isatty():
            tty.setraw(self.input_tty.fileno())

        if self._use_alt_screen:
            self._renderer.enter_alt_screen()
        if self._mouse_all_motion:
            self._renderer.enable_mouse(all_motion=True)
        elif self._mouse_cell_motion:
            self._renderer.enable_mouse(all_motion=False)
        self._renderer.hide_cursor()

        if self._bracketed_paste:
            self.output.write("\x1b[?2004h")
            self.output.flush()

        if self._report_focus:
            self.output.write("\x1b[?1004h")
            self.output.flush()

        self._renderer.start()
        self._renderer.repaint()
        self._render()

    def _handle_exec(self, msg: ExecMsg) -> None:
        """Suspend the TUI, run an external process, then resume.

        The terminal is handed back to the OS for the duration of the
        subprocess so it has full, interactive terminal access.  After the
        process exits the TUI is restored and the callback (if any) is
        called; its return value is enqueued for the event loop.

        Not supported on Windows — silently returns without running the
        command if SIGTSTP is absent (used as a Unix proxy here).
        """
        import subprocess as _sp

        self.release_terminal()
        err: Optional[Exception] = None
        try:
            _sp.run(msg.exec_cmd.args, **msg.exec_cmd.popen_kwargs)
        except Exception as exc:
            err = exc
        finally:
            self.restore_terminal()

        if msg.callback is not None:
            result = msg.callback(err)
            if result is not None:
                self._msg_queue.put(result)

    def _suspend(self) -> None:
        """Restore the terminal, suspend the process via SIGTSTP, then resume.

        Called when SuspendMsg is received.  The sequence is:
          1. Stop the renderer and restore the terminal to cooked mode.
          2. Register a SIGCONT handler and send SIGTSTP to the current process.
          3. The OS suspends the entire process (all threads pause here).
          4. When the user runs `fg` / sends SIGCONT, the process resumes.
          5. Re-enter raw mode, restart the renderer, repaint, send ResumeMsg.

        Only available on Unix.  On platforms without SIGTSTP the method
        returns immediately without doing anything.
        """
        if not hasattr(signal, 'SIGTSTP'):
            return

        # 1. Stop the renderer without a final flush and restore the terminal.
        self._renderer.kill()
        self._renderer.show_cursor()
        self._renderer.exit_alt_screen()
        self._renderer.disable_mouse()

        if self._bracketed_paste:
            self.output.write("\x1b[?2004l")
            self.output.flush()

        if self._old_termios is not None and self.input_tty.isatty():
            termios.tcsetattr(
                self.input_tty.fileno(), termios.TCSADRAIN, self._old_termios
            )

        # 2. Register SIGCONT handler and suspend.
        sigcont_received = Event()
        original_sigcont = signal.getsignal(signal.SIGCONT)

        def on_sigcont(signum: int, frame: Any) -> None:
            sigcont_received.set()

        signal.signal(signal.SIGCONT, on_sigcont)
        os.kill(os.getpid(), signal.SIGTSTP)

        # 3–4. The process is stopped here until SIGCONT is received.
        sigcont_received.wait()
        signal.signal(signal.SIGCONT, original_sigcont)

        # 5. Re-enter raw mode and restart all terminal features.
        if self.input_tty.isatty():
            tty.setraw(self.input_tty.fileno())

        if self._use_alt_screen:
            self._renderer.enter_alt_screen()
        if self._mouse_all_motion:
            self._renderer.enable_mouse(all_motion=True)
        elif self._mouse_cell_motion:
            self._renderer.enable_mouse(all_motion=False)
        self._renderer.hide_cursor()

        if self._bracketed_paste:
            self.output.write("\x1b[?2004h")
            self.output.flush()

        self._renderer.start()
        self._renderer.repaint()
        self._render()

        self._msg_queue.put(ResumeMsg())

    def _start_input_reader(self) -> None:
        """Start the input reader thread."""
        def read_input() -> None:
            try:
                fd = self.input_tty.fileno()
            except Exception:
                # The input stream is not a real TTY (e.g. redirected in tests).
                # Skip input reading entirely; the program can still be driven
                # via Program.send() / Program.quit() / Program.kill().
                return
            # Bracketed paste accumulation state.
            in_paste = False
            paste_buf: list[str] = []

            while not self._quit.is_set():
                # Use select to avoid blocking
                if sys.platform != 'win32':
                    readable, _, _ = select.select([fd], [], [], 0.1)
                    if not readable:
                        continue

                try:
                    # Read available input
                    data = os.read(fd, 256)
                    if not data:
                        continue

                    # Focus / blur sequences (sent when report_focus=True).
                    if self._report_focus:
                        if data == b"\x1b[I":
                            self._msg_queue.put(FocusMsg())
                            continue
                        if data == b"\x1b[O":
                            self._msg_queue.put(BlurMsg())
                            continue

                    # Bracketed paste sequences.
                    if self._bracketed_paste:
                        text = data.decode('utf-8', errors='replace')
                        if '\x1b[200~' in text:
                            # Paste start: emit PasteStartMsg and buffer
                            # everything after the marker.
                            in_paste = True
                            paste_buf.clear()
                            self._msg_queue.put(PasteStartMsg())
                            after = text.split('\x1b[200~', 1)[1]
                            if '\x1b[201~' in after:
                                content, _ = after.split('\x1b[201~', 1)
                                paste_buf.append(content)
                                self._msg_queue.put(PasteEndMsg())
                                self._msg_queue.put(PasteMsg("".join(paste_buf)))
                                in_paste = False
                                paste_buf.clear()
                            else:
                                paste_buf.append(after)
                            continue
                        if in_paste:
                            text = data.decode('utf-8', errors='replace')
                            if '\x1b[201~' in text:
                                content, _ = text.split('\x1b[201~', 1)
                                paste_buf.append(content)
                                self._msg_queue.put(PasteEndMsg())
                                self._msg_queue.put(PasteMsg("".join(paste_buf)))
                                in_paste = False
                                paste_buf.clear()
                            else:
                                paste_buf.append(text)
                            continue

                    # Try to parse as mouse event first
                    mouse_event = parse_mouse_event(data)
                    if mouse_event:
                        self._msg_queue.put(MouseMsg(
                            x=mouse_event.x,
                            y=mouse_event.y,
                            button=mouse_event.button.value,
                            action=mouse_event.action.name.lower(),
                            alt=mouse_event.alt,
                            ctrl=mouse_event.ctrl,
                            shift=mouse_event.shift,
                        ))
                        continue

                    # Parse as key
                    key = parse_key(data)
                    if key:
                        self._msg_queue.put(KeyMsg(key=key))

                except OSError:
                    break

        self._input_thread = Thread(target=read_input, daemon=True)
        self._input_thread.start()


# Convenience functions for creating programs with options
def with_alt_screen() -> Callable[[Program], None]:
    """Option to use alternate screen buffer."""
    def option(p: Program) -> None:
        p._use_alt_screen = True
    return option


def with_mouse_cell_motion() -> Callable[[Program], None]:
    """Option to enable mouse cell motion tracking."""
    def option(p: Program) -> None:
        p._mouse_cell_motion = True
    return option


def with_mouse_all_motion() -> Callable[[Program], None]:
    """Option to enable mouse all motion tracking."""
    def option(p: Program) -> None:
        p._mouse_all_motion = True
    return option
