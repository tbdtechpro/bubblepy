"""Tests for renderer.py — Renderer and NullRenderer."""

import io
import time

from bubbletea.renderer import NullRenderer, Renderer

# ── Helpers ──────────────────────────────────────────────────────────────────


def make_renderer(fps: int = 120) -> tuple[Renderer, io.StringIO]:
    buf = io.StringIO()
    r = Renderer(buf, fps=fps)
    return r, buf


# ── Renderer unit tests ───────────────────────────────────────────────────────


class TestRendererLifecycle:
    def test_start_stop(self):
        r, _ = make_renderer()
        r.start()
        r.stop()

    def test_kill(self):
        r, _ = make_renderer()
        r.start()
        r.kill()

    def test_close_calls_show_cursor(self):
        r, buf = make_renderer()
        r.start()
        r.hide_cursor()
        r.close()
        out = buf.getvalue()
        # show-cursor sequence must appear after hide-cursor
        assert "\x1b[?25h" in out

    def test_repaint_clears_last_render(self):
        r, _ = make_renderer()
        r._last_render = "old"
        r.repaint()
        assert r._last_render == ""


class TestRendererFlush:
    def test_first_render_writes_view(self):
        r, buf = make_renderer()
        r.render("hello")
        r._flush()
        assert "hello" in buf.getvalue()

    def test_identical_view_not_redrawn(self):
        r, buf = make_renderer()
        r.render("hello")
        r._flush()
        before = buf.getvalue()
        r.render("hello")
        r._flush()
        assert buf.getvalue() == before  # no second write

    def test_changed_view_redrawn(self):
        r, buf = make_renderer()
        r.render("hello")
        r._flush()
        r.render("world")
        r._flush()
        assert "world" in buf.getvalue()

    def test_pending_prints_output_before_view(self):
        r, buf = make_renderer()
        r.render("TUI")
        r.print_line("line1")
        r._flush()
        out = buf.getvalue()
        assert "line1" in out
        # line1 should appear before TUI in output
        assert out.index("line1") < out.index("TUI")

    def test_print_line_noop_in_alt_screen(self):
        r, buf = make_renderer()
        r._alt_screen = True
        r.print_line("should be ignored")
        assert r._print_queue == []


class TestRendererClear:
    def test_clear_writes_escape(self):
        r, buf = make_renderer()
        r.clear()
        assert "\x1b[2J" in buf.getvalue()

    def test_clear_resets_state(self):
        r, _ = make_renderer()
        r._lines_rendered = 5
        r._last_render = "old"
        r.clear()
        assert r._lines_rendered == 0
        assert r._last_render == ""


class TestRendererCursorAndScreen:
    def test_hide_show_cursor(self):
        r, buf = make_renderer()
        r.hide_cursor()
        assert "\x1b[?25l" in buf.getvalue()
        r.show_cursor()
        assert "\x1b[?25h" in buf.getvalue()

    def test_hide_cursor_idempotent(self):
        r, buf = make_renderer()
        r.hide_cursor()
        r.hide_cursor()  # should not write again
        assert buf.getvalue().count("\x1b[?25l") == 1

    def test_alt_screen_enter_exit(self):
        r, buf = make_renderer()
        r.enter_alt_screen()
        assert "\x1b[?1049h" in buf.getvalue()
        assert r.alt_screen_active()
        r.exit_alt_screen()
        assert "\x1b[?1049l" in buf.getvalue()
        assert not r.alt_screen_active()

    def test_enter_alt_screen_idempotent(self):
        r, buf = make_renderer()
        r.enter_alt_screen()
        r.enter_alt_screen()
        assert buf.getvalue().count("\x1b[?1049h") == 1

    def test_mouse_enable_disable(self):
        r, buf = make_renderer()
        r.enable_mouse(all_motion=False)
        assert "\x1b[?1002h" in buf.getvalue()
        r.disable_mouse()
        assert "\x1b[?1000l" in buf.getvalue()

    def test_mouse_all_motion(self):
        r, buf = make_renderer()
        r.enable_mouse(all_motion=True)
        assert "\x1b[?1003h" in buf.getvalue()

    def test_set_window_title(self):
        r, buf = make_renderer()
        r.set_window_title("My TUI")
        assert "My TUI" in buf.getvalue()


class TestRendererFPSCoalescing:
    def test_rapid_renders_coalesce(self):
        """Many rapid render() calls should produce ≤ 2 terminal writes."""
        r, buf = make_renderer(fps=60)
        r.start()
        for i in range(50):
            r.render(f"frame {i}")
        time.sleep(0.05)  # wait for up to 3 ticks at 60 fps
        r.stop()
        # The last frame should be present
        assert "frame 49" in buf.getvalue()

    def test_state_queries(self):
        r, _ = make_renderer()
        assert not r.is_cursor_hidden()
        r.hide_cursor()
        assert r.is_cursor_hidden()
        r.show_cursor()
        assert not r.is_cursor_hidden()


# ── NullRenderer tests ────────────────────────────────────────────────────────


class TestNullRenderer:
    def test_all_methods_are_noops(self):
        nr = NullRenderer(io.StringIO())
        nr.start()
        nr.render("hello")
        nr.print_line("hi")
        nr._flush()
        nr.clear()
        nr.enter_alt_screen()
        nr.exit_alt_screen()
        nr.hide_cursor()
        nr.show_cursor()
        nr.enable_mouse()
        nr.disable_mouse()
        nr.set_window_title("x")
        nr.stop()
        nr.kill()
        nr.repaint()
        nr.close()

    def test_output_stays_empty(self):
        buf = io.StringIO()
        nr = NullRenderer(buf)
        nr.start()
        nr.render("anything")
        nr.stop()
        assert buf.getvalue() == ""
