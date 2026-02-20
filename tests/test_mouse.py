"""Tests for mouse.py — parse_mouse_event()."""

import pytest

from bubbletea.mouse import (
    parse_mouse_event,
    MouseButton,
    MouseAction,
    MouseEvent,
)


def _sgr(cb: int, cx: int, cy: int, release: bool = False) -> bytes:
    """Build an SGR mouse escape sequence."""
    term = "m" if release else "M"
    return f"\x1b[<{cb};{cx};{cy}{term}".encode()


def _x10(btn: int, col: int, row: int) -> bytes:
    """Build an X10 mouse escape sequence (6 bytes)."""
    return b"\x1b[M" + bytes([btn + 0x20, col + 0x21, row + 0x21])


class TestSGRMouseParsing:
    def test_left_press(self):
        ev = parse_mouse_event(_sgr(0, 10, 5))
        assert ev is not None
        assert ev.button == MouseButton.LEFT
        assert ev.action == MouseAction.PRESS
        assert ev.x == 9   # 1-based → 0-based
        assert ev.y == 4

    def test_left_release(self):
        ev = parse_mouse_event(_sgr(0, 10, 5, release=True))
        assert ev is not None
        assert ev.action == MouseAction.RELEASE

    def test_right_press(self):
        ev = parse_mouse_event(_sgr(2, 1, 1))
        assert ev is not None
        assert ev.button == MouseButton.RIGHT

    def test_middle_press(self):
        ev = parse_mouse_event(_sgr(1, 1, 1))
        assert ev is not None
        assert ev.button == MouseButton.MIDDLE

    def test_wheel_up(self):
        ev = parse_mouse_event(_sgr(64, 1, 1))
        assert ev is not None
        assert ev.button == MouseButton.WHEEL_UP
        assert ev.action == MouseAction.PRESS

    def test_wheel_down(self):
        ev = parse_mouse_event(_sgr(65, 1, 1))
        assert ev is not None
        assert ev.button == MouseButton.WHEEL_DOWN

    def test_cell_motion(self):
        ev = parse_mouse_event(_sgr(32, 5, 5))  # cb bit 5 = motion
        assert ev is not None
        assert ev.action == MouseAction.MOTION

    def test_shift_modifier(self):
        ev = parse_mouse_event(_sgr(4, 1, 1))   # bit 2 = shift
        assert ev is not None
        assert ev.shift is True

    def test_alt_modifier(self):
        ev = parse_mouse_event(_sgr(8, 1, 1))   # bit 3 = alt
        assert ev is not None
        assert ev.alt is True

    def test_ctrl_modifier(self):
        ev = parse_mouse_event(_sgr(16, 1, 1))  # bit 4 = ctrl
        assert ev is not None
        assert ev.ctrl is True

    def test_combined_modifiers(self):
        ev = parse_mouse_event(_sgr(4 | 8 | 16, 1, 1))
        assert ev is not None
        assert ev.shift and ev.alt and ev.ctrl

    def test_no_match_returns_none(self):
        assert parse_mouse_event(b"hello") is None

    def test_malformed_sgr_returns_none(self):
        assert parse_mouse_event(b"\x1b[<abc;def;ghiM") is None


class TestX10MouseParsing:
    def test_left_press(self):
        ev = parse_mouse_event(_x10(0, 5, 3))
        assert ev is not None
        assert ev.button == MouseButton.LEFT
        assert ev.action == MouseAction.PRESS
        assert ev.x == 5
        assert ev.y == 3

    def test_right_press(self):
        ev = parse_mouse_event(_x10(2, 1, 1))
        assert ev is not None
        assert ev.button == MouseButton.RIGHT

    def test_release(self):
        ev = parse_mouse_event(_x10(3, 5, 5))  # btn=3 means release
        assert ev is not None
        assert ev.action == MouseAction.RELEASE
        assert ev.button == MouseButton.NONE

    def test_alt_modifier(self):
        ev = parse_mouse_event(_x10(0 | 8, 1, 1))  # bit 3 = alt
        assert ev is not None
        assert ev.alt is True

    def test_shift_modifier(self):
        ev = parse_mouse_event(_x10(0 | 4, 1, 1))  # bit 2 = shift
        assert ev is not None
        assert ev.shift is True

    def test_origin_coordinates(self):
        ev = parse_mouse_event(_x10(0, 0, 0))
        assert ev is not None
        assert ev.x == 0
        assert ev.y == 0

    def test_too_short_x10_not_parsed(self):
        # Only 5 bytes (not 6) should not be parsed as X10
        assert parse_mouse_event(b"\x1b[M\x20\x21") is None
