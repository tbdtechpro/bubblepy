"""Tests for screen.py — command factories and message types."""

import pytest

import bubbletea as tea
from bubbletea.screen import (
    enter_alt_screen,
    exit_alt_screen,
    enable_mouse_cell_motion,
    enable_mouse_all_motion,
    disable_mouse,
    show_cursor,
    hide_cursor,
    suspend,
    EnterAltScreenMsg,
    ExitAltScreenMsg,
    EnableMouseCellMotionMsg,
    EnableMouseAllMotionMsg,
    DisableMouseMsg,
    ShowCursorMsg,
    HideCursorMsg,
)
from bubbletea.messages import SuspendMsg


class TestScreenCommandFactories:
    def test_enter_alt_screen(self):
        cmd = enter_alt_screen()
        assert callable(cmd)
        assert isinstance(cmd(), EnterAltScreenMsg)

    def test_exit_alt_screen(self):
        cmd = exit_alt_screen()
        assert callable(cmd)
        assert isinstance(cmd(), ExitAltScreenMsg)

    def test_enable_mouse_cell_motion(self):
        cmd = enable_mouse_cell_motion()
        assert isinstance(cmd(), EnableMouseCellMotionMsg)

    def test_enable_mouse_all_motion(self):
        cmd = enable_mouse_all_motion()
        assert isinstance(cmd(), EnableMouseAllMotionMsg)

    def test_disable_mouse(self):
        cmd = disable_mouse()
        assert isinstance(cmd(), DisableMouseMsg)

    def test_show_cursor(self):
        cmd = show_cursor()
        assert isinstance(cmd(), ShowCursorMsg)

    def test_hide_cursor(self):
        cmd = hide_cursor()
        assert isinstance(cmd(), HideCursorMsg)

    def test_suspend(self):
        cmd = suspend()
        assert callable(cmd)
        assert isinstance(cmd(), SuspendMsg)

    def test_all_return_callables(self):
        factories = [
            enter_alt_screen,
            exit_alt_screen,
            enable_mouse_cell_motion,
            enable_mouse_all_motion,
            disable_mouse,
            show_cursor,
            hide_cursor,
            suspend,
        ]
        for factory in factories:
            cmd = factory()
            assert callable(cmd), f"{factory.__name__} did not return a callable"

    def test_message_types_are_msg_subclasses(self):
        for MsgType in [
            EnterAltScreenMsg,
            ExitAltScreenMsg,
            EnableMouseCellMotionMsg,
            EnableMouseAllMotionMsg,
            DisableMouseMsg,
            ShowCursorMsg,
            HideCursorMsg,
        ]:
            assert issubclass(MsgType, tea.Msg)
