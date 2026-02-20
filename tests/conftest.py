"""Shared pytest fixtures for Bubble Tea tests."""

import io
import queue
from typing import Optional

import pytest

import bubbletea as tea
from bubbletea.renderer import NullRenderer

# ── Fixtures ────────────────────────────────────────────────────────────────


@pytest.fixture
def null_renderer() -> NullRenderer:
    """A NullRenderer backed by an in-memory StringIO."""
    return NullRenderer(io.StringIO())


@pytest.fixture
def capture_queue() -> queue.Queue:
    """A fresh Queue for capturing messages in tests."""
    return queue.Queue()


class _EchoModel(tea.Model):
    """Minimal model that records the last message it received."""

    def __init__(self) -> None:
        self.last_msg: Optional[tea.Msg] = None
        self.view_text = "hello"

    def init(self) -> Optional[tea.Cmd]:
        return None

    def update(self, msg: tea.Msg):  # type: ignore[override]
        self.last_msg = msg
        if isinstance(msg, tea.KeyMsg) and msg.key == "q":
            return self, tea.quit_cmd
        return self, None

    def view(self) -> str:
        return self.view_text


@pytest.fixture
def echo_model() -> _EchoModel:
    """A minimal Model that records messages and quits on 'q'."""
    return _EchoModel()


def make_program(model: tea.Model, **kwargs) -> tea.Program:
    """Create a headless Program with NullRenderer for testing."""
    kwargs.setdefault("output", io.StringIO())
    kwargs.setdefault("use_null_renderer", True)
    return tea.Program(model, **kwargs)
