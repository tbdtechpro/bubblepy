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
    QuitMsg, FocusMsg, BlurMsg,
    ClearScreenMsg, SetWindowTitleMsg,
    SuspendMsg, ResumeMsg,
)
from .keys import parse_key
from .mouse import parse_mouse_event
from .renderer import Renderer, NullRenderer
from .commands import Cmd, BatchMsg, SequenceMsg
from .screen import (
    EnterAltScreenMsg, ExitAltScreenMsg,
    EnableMouseCellMotionMsg, EnableMouseAllMotionMsg, DisableMouseMsg,
    ShowCursorMsg, HideCursorMsg,
)


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
    ):
        """
        Initialize a new Program.
        
        Args:
            model: The initial model
            input_tty: Input file (defaults to stdin)
            output: Output file (defaults to stdout)
            alt_screen: Whether to use alternate screen buffer
            mouse_cell_motion: Enable mouse cell motion tracking
            mouse_all_motion: Enable mouse all motion tracking
            bracketed_paste: Enable bracketed paste mode
            fps: Frames per second for rendering
        """
        self.model = model
        self.input_tty = input_tty or sys.stdin
        self.output = output or sys.stdout
        self._use_alt_screen = alt_screen
        self._mouse_cell_motion = mouse_cell_motion
        self._mouse_all_motion = mouse_all_motion
        self._bracketed_paste = bracketed_paste
        
        self._renderer = Renderer(self.output, fps)
        self._msg_queue: Queue[Msg] = Queue()
        self._quit = Event()
        self._running = False
        self._old_termios: Optional[list] = None
        self._input_thread: Optional[Thread] = None
    
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
            cmd = self.model.init()
            if cmd is not None:
                self._execute_cmd(cmd)
            self._render()

            # Start input reader thread
            self._start_input_reader()
            
            # Main event loop
            self._event_loop()
            
        finally:
            self._cleanup()
        
        return self.model
    
    def quit(self) -> None:
        """Signal the program to quit."""
        self._quit.set()
        self._msg_queue.put(QuitMsg())
    
    def send(self, msg: Msg) -> None:
        """Send a message to the program."""
        self._msg_queue.put(msg)
    
    def _event_loop(self) -> None:
        """Main event loop."""
        while not self._quit.is_set():
            try:
                # Wait for a message
                msg = self._msg_queue.get(timeout=0.1)
            except Empty:
                continue

            # Lifecycle
            if isinstance(msg, QuitMsg):
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
        """Run a single command in a daemon thread and enqueue its result."""
        def run() -> None:
            try:
                result = cmd()
                if result is not None:
                    self._msg_queue.put(result)
            except Exception:
                pass

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

        def handle_term(signum: int, frame: Any) -> None:
            self._msg_queue.put(QuitMsg())

        signal.signal(signal.SIGWINCH, handle_resize)
        signal.signal(signal.SIGTERM, handle_term)

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
        def read_input():
            fd = self.input_tty.fileno()
            
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
