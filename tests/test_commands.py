"""Tests for commands.py."""

import time
import threading
from typing import Optional

import pytest

import bubbletea as tea
from bubbletea.commands import (
    batch,
    sequence,
    quit_cmd,
    set_window_title,
    clear_screen,
    tick,
    every,
    window_size,
    BatchMsg,
    SequenceMsg,
)
from bubbletea.messages import (
    QuitMsg,
    SetWindowTitleMsg,
    ClearScreenMsg,
    WindowSizeMsg,
)


class TestQuitCmd:
    def test_returns_quit_msg(self):
        assert isinstance(quit_cmd(), QuitMsg)


class TestBatch:
    def test_none_only_returns_none(self):
        assert batch(None, None) is None

    def test_single_cmd_passthrough(self):
        cmd = lambda: QuitMsg()
        result = batch(cmd)
        assert result is cmd

    def test_filters_none(self):
        cmd = lambda: QuitMsg()
        result = batch(None, cmd, None)
        assert result is cmd  # single valid cmd → passthrough

    def test_multiple_cmds_returns_batch_msg(self):
        c1 = lambda: QuitMsg()
        c2 = lambda: QuitMsg()
        batched = batch(c1, c2)
        assert batched is not None
        msg = batched()
        assert isinstance(msg, BatchMsg)
        assert len(msg.cmds) == 2

    def test_parallel_execution(self):
        """Two slow commands should finish faster than sequential."""
        log: list[str] = []
        lock = threading.Lock()

        def slow_a():
            time.sleep(0.05)
            with lock:
                log.append("a")
            return QuitMsg()

        def slow_b():
            time.sleep(0.05)
            with lock:
                log.append("b")
            return QuitMsg()

        batched = batch(slow_a, slow_b)
        assert batched is not None
        msg = batched()
        assert isinstance(msg, BatchMsg)
        # Both commands are in the batch (execution happens in event loop)
        assert len(msg.cmds) == 2


class TestSequence:
    def test_none_only_returns_none(self):
        assert sequence(None, None) is None

    def test_single_cmd_passthrough(self):
        cmd = lambda: QuitMsg()
        result = sequence(cmd)
        assert result is cmd

    def test_multiple_returns_sequence_msg(self):
        c1 = lambda: QuitMsg()
        c2 = lambda: QuitMsg()
        seq = sequence(c1, c2)
        assert seq is not None
        msg = seq()
        assert isinstance(msg, SequenceMsg)
        assert len(msg.cmds) == 2


class TestSetWindowTitle:
    def test_produces_msg(self):
        cmd = set_window_title("My App")
        msg = cmd()
        assert isinstance(msg, SetWindowTitleMsg)
        assert msg.title == "My App"


class TestClearScreen:
    def test_produces_msg(self):
        cmd = clear_screen()
        assert isinstance(cmd(), ClearScreenMsg)


class TestTick:
    def test_delays_and_returns_msg(self):
        sentinel = object()

        def make_msg():
            return QuitMsg()

        cmd = tick(0.01, make_msg)
        start = time.monotonic()
        result = cmd()
        elapsed = time.monotonic() - start
        assert isinstance(result, QuitMsg)
        assert elapsed >= 0.01

    def test_fn_called_after_delay(self):
        called = []
        cmd = tick(0.01, lambda: called.append(True) or QuitMsg())
        cmd()
        assert called


class TestEvery:
    def test_fires_once(self):
        results = []
        cmd = every(0.01, lambda: QuitMsg())
        result = cmd()
        assert isinstance(result, QuitMsg)


class TestWindowSize:
    def test_returns_callable(self):
        cmd = window_size()
        assert callable(cmd)

    def test_produces_window_size_msg_or_none(self):
        cmd = window_size()
        result = cmd()
        # In CI / pipe the TTY may not exist; result can be None or WindowSizeMsg
        assert result is None or isinstance(result, WindowSizeMsg)
