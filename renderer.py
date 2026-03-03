"""Terminal renderer for Bubble Tea."""

import sys
import threading
from typing import Optional, TextIO


class Renderer:
    """Handles rendering output to the terminal.

    Rendering is FPS-capped: render() queues a pending view but does not
    write to the terminal immediately.  A background ticker thread wakes
    up at most fps times per second and flushes the pending view only if
    it changed from the last rendered frame.  This coalesces rapid model
    updates into a single terminal write per frame.

    All output writes and shared state mutations are protected by a single
    lock so the ticker thread and the event-loop thread cannot interleave
    their writes.
    """

    def __init__(
        self,
        output: TextIO = sys.stdout,
        fps: int = 60,
    ):
        self.output = output
        self.fps = max(1, min(fps, 120))  # clamp to [1, 120]

        self._lock = threading.Lock()
        self._pending_view: Optional[str] = None
        self._last_render: str = ""
        self._lines_rendered: int = 0
        self._cursor_hidden: bool = False
        self._alt_screen: bool = False
        self._print_queue: list[str] = []

        self._stop_event = threading.Event()
        self._ticker_thread: Optional[threading.Thread] = None

    # ── Lifecycle ───────────────────────────────────────────────────────────

    def start(self) -> None:
        """Start the FPS-capped rendering ticker in a daemon thread."""
        self._stop_event.clear()
        self._ticker_thread = threading.Thread(
            target=self._ticker_loop,
            daemon=True,
            name="bubbletea-renderer",
        )
        self._ticker_thread.start()

    def stop(self) -> None:
        """Stop the ticker thread and perform one final flush."""
        self._stop_event.set()
        if self._ticker_thread is not None:
            self._ticker_thread.join(timeout=1.0)
            self._ticker_thread = None
        self._flush()

    def kill(self) -> None:
        """Stop the ticker thread immediately without a final flush."""
        self._stop_event.set()
        if self._ticker_thread is not None:
            self._ticker_thread.join(timeout=0.5)
            self._ticker_thread = None

    def repaint(self) -> None:
        """Force a full repaint on the next tick by discarding the last frame."""
        with self._lock:
            self._last_render = ""

    def close(self) -> None:
        """Stop the ticker and restore default terminal state."""
        self.stop()
        self.show_cursor()
        self.exit_alt_screen()
        self.disable_mouse()

    # ── State queries ───────────────────────────────────────────────────────

    def alt_screen_active(self) -> bool:
        """Return whether the alternate screen buffer is currently active."""
        return self._alt_screen

    def is_cursor_hidden(self) -> bool:
        """Return whether the cursor is currently hidden."""
        return self._cursor_hidden

    # ── Rendering ───────────────────────────────────────────────────────────

    def render(self, view: str) -> None:
        """Queue a view for rendering at the next tick.

        Does not write to the terminal immediately.  The FPS ticker calls
        _flush() at regular intervals to coalesce rapid updates into a
        single terminal write per frame.
        """
        with self._lock:
            self._pending_view = view

    def print_line(self, line: str) -> None:
        """Schedule a line to be printed above the TUI on the next flush.

        Lines appear above the managed TUI area and scroll into the terminal's
        scrollback buffer, persisting across re-renders.  In alt-screen mode
        this is a no-op (no scrollback exists in the alternate screen).
        """
        if self._alt_screen:
            return
        with self._lock:
            self._print_queue.append(line)

    def _flush(self) -> None:
        """Write pending print lines and the current view to the terminal.

        Print lines are output first (above the TUI); each becomes part of
        the terminal's scrollback buffer.  The TUI is then redrawn below
        them.  If neither prints nor a view change are pending, returns
        immediately.
        """
        with self._lock:
            pending_prints = self._print_queue[:]
            self._print_queue.clear()

            view = self._pending_view
            # Fix: normalize trailing \n before the change-detection comparison
            # so that "hello" and "hello\n" are treated as the same view.
            if view is not None and not view.endswith("\n"):
                view += "\n"
            view_changed = view is not None and view != self._last_render

            if not pending_prints and not view_changed:
                return

            # Use the latest view; fall back to the last rendered frame
            # so that we can still output print lines even when the view
            # itself has not changed.
            if view is None:
                view = self._last_render

            # Erase the previous TUI render and reset cursor to column 0.
            if self._lines_rendered > 0:
                # Move up N lines (erasing each) then carriage-return to col 0.
                self.output.write("\x1b[A\x1b[2K" * self._lines_rendered + "\r")
            else:
                self.output.write("\r\x1b[2K")

            # Write print lines above the TUI.  Each scrolls into history.
            for line in pending_prints:
                self.output.write(line + "\r\n")

            # Fix: in raw mode tty.setraw() disables OPOST/ONLCR, so \n is a
            # pure line feed with no carriage return.  Convert every \n to \r\n.
            self.output.write(view.replace("\n", "\r\n"))
            self.output.flush()

            self._lines_rendered = view.count("\n")
            if view_changed:
                self._last_render = view

    def _ticker_loop(self) -> None:
        """Sleep for one frame interval then flush.  Repeat until stopped."""
        interval = 1.0 / self.fps
        while not self._stop_event.wait(timeout=interval):
            self._flush()

    # ── Terminal control (immediate, not tick-deferred) ─────────────────────

    def clear(self) -> None:
        """Clear the screen and reset all render state."""
        with self._lock:
            self.output.write("\x1b[2J\x1b[H")
            self.output.flush()
            self._lines_rendered = 0
            self._last_render = ""
            self._pending_view = None

    def enter_alt_screen(self) -> None:
        """Enter the alternate screen buffer."""
        if not self._alt_screen:
            with self._lock:
                self.output.write("\x1b[?1049h")
                self.output.flush()
                self._alt_screen = True
                self._lines_rendered = 0
                self._last_render = ""
                self._pending_view = None

    def exit_alt_screen(self) -> None:
        """Exit the alternate screen buffer."""
        if self._alt_screen:
            with self._lock:
                self.output.write("\x1b[?1049l")
                self.output.flush()
                self._alt_screen = False

    def hide_cursor(self) -> None:
        """Hide the terminal cursor."""
        if not self._cursor_hidden:
            with self._lock:
                self.output.write("\x1b[?25l")
                self.output.flush()
                self._cursor_hidden = True

    def show_cursor(self) -> None:
        """Show the terminal cursor."""
        if self._cursor_hidden:
            with self._lock:
                self.output.write("\x1b[?25h")
                self.output.flush()
                self._cursor_hidden = False

    def enable_mouse(self, all_motion: bool = False) -> None:
        """Enable mouse tracking."""
        with self._lock:
            if all_motion:
                self.output.write("\x1b[?1003h")  # all motion
            else:
                self.output.write("\x1b[?1002h")  # cell motion
            self.output.write("\x1b[?1006h")  # SGR extended mode
            self.output.flush()

    def disable_mouse(self) -> None:
        """Disable mouse tracking."""
        with self._lock:
            self.output.write("\x1b[?1000l\x1b[?1002l\x1b[?1003l\x1b[?1006l")
            self.output.flush()

    def set_window_title(self, title: str) -> None:
        """Set the terminal window title."""
        with self._lock:
            self.output.write(f"\x1b]0;{title}\x07")
            self.output.flush()


class NullRenderer(Renderer):
    """A no-op renderer used for testing and headless programs."""

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def kill(self) -> None:
        pass

    def repaint(self) -> None:
        pass

    def close(self) -> None:
        pass

    def render(self, view: str) -> None:
        pass

    def print_line(self, line: str) -> None:
        pass

    def _flush(self) -> None:
        pass

    def clear(self) -> None:
        pass

    def enter_alt_screen(self) -> None:
        pass

    def exit_alt_screen(self) -> None:
        pass

    def hide_cursor(self) -> None:
        pass

    def show_cursor(self) -> None:
        pass

    def enable_mouse(self, all_motion: bool = False) -> None:
        pass

    def disable_mouse(self) -> None:
        pass

    def set_window_title(self, title: str) -> None:
        pass
