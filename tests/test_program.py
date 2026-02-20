"""Integration tests for Program lifecycle."""

import io
import threading
import time
from typing import Optional

import pytest

import bubbletea as tea
from bubbletea.renderer import NullRenderer
from tests.conftest import make_program


# ── Minimal models ────────────────────────────────────────────────────────────


class QuitOnFirstMsg(tea.Model):
    """Quits immediately after receiving any message from init."""

    def __init__(self) -> None:
        self.received: list[type] = []

    def init(self) -> Optional[tea.Cmd]:
        return tea.quit_cmd  # quit right away

    def update(self, msg: tea.Msg):  # type: ignore[override]
        self.received.append(type(msg))
        return self, None

    def view(self) -> str:
        return "bye"


class EchoQuitModel(tea.Model):
    """Records messages; quits on KeyMsg('q')."""

    def __init__(self) -> None:
        self.msgs: list[tea.Msg] = []

    def init(self) -> Optional[tea.Cmd]:
        return None

    def update(self, msg: tea.Msg):  # type: ignore[override]
        self.msgs.append(msg)
        if isinstance(msg, tea.KeyMsg) and msg.key == "q":
            return self, tea.quit_cmd
        return self, None

    def view(self) -> str:
        return f"msgs={len(self.msgs)}"


class SenderModel(tea.Model):
    """Receives injected messages; quits on QuitMsg."""

    def __init__(self) -> None:
        self.msgs: list[tea.Msg] = []

    def init(self) -> Optional[tea.Cmd]:
        return None

    def update(self, msg: tea.Msg):  # type: ignore[override]
        self.msgs.append(msg)
        return self, None

    def view(self) -> str:
        return "ok"


class InitCmdModel(tea.Model):
    """Runs a command from init(), quits after receiving its result."""

    def __init__(self) -> None:
        self.got_init_result = False

    def init(self) -> Optional[tea.Cmd]:
        def cmd() -> tea.Msg:
            return tea.KeyMsg(key="x")
        return cmd

    def update(self, msg: tea.Msg):  # type: ignore[override]
        if isinstance(msg, tea.KeyMsg) and msg.key == "x":
            self.got_init_result = True
            return self, tea.quit_cmd
        return self, None

    def view(self) -> str:
        return "init-cmd-model"


class FilterTestModel(tea.Model):
    """Receives messages; quits immediately."""

    def __init__(self) -> None:
        self.msgs: list[tea.Msg] = []

    def init(self) -> Optional[tea.Cmd]:
        return tea.quit_cmd

    def update(self, msg: tea.Msg):  # type: ignore[override]
        self.msgs.append(msg)
        return self, None

    def view(self) -> str:
        return "filter"


# ── Tests ─────────────────────────────────────────────────────────────────────


class TestProgramLifecycle:
    def test_init_quit_cmd_exits(self):
        """Program that returns quit_cmd from init() should run() cleanly."""
        model = QuitOnFirstMsg()
        p = make_program(model)
        final = p.run()
        assert final is model

    def test_init_cmd_message_delivered(self):
        """Command returned from init() must reach update()."""
        model = InitCmdModel()
        p = make_program(model)
        p.run()
        assert model.got_init_result

    def test_final_model_returned(self):
        model = QuitOnFirstMsg()
        p = make_program(model)
        result = p.run()
        assert isinstance(result, QuitOnFirstMsg)


class TestProgramSend:
    def test_send_injects_message(self):
        """Program.send() should deliver a message to update()."""
        model = SenderModel()
        p = make_program(model)

        injected = tea.KeyMsg(key="z")

        def driver() -> None:
            time.sleep(0.05)
            p.send(injected)
            time.sleep(0.05)
            p.quit()

        t = threading.Thread(target=driver, daemon=True)
        t.start()
        p.run()
        t.join()

        assert injected in model.msgs


class TestProgramKill:
    def test_kill_raises_err_program_killed(self):
        """kill() should cause run() to raise ErrProgramKilled."""
        model = SenderModel()
        p = make_program(model)

        def driver() -> None:
            time.sleep(0.05)
            p.kill()

        t = threading.Thread(target=driver, daemon=True)
        t.start()

        with pytest.raises(tea.ErrProgramKilled):
            p.run()
        t.join()


class TestProgramWait:
    def test_wait_blocks_until_done(self):
        """wait() must not return before run() completes."""
        model = QuitOnFirstMsg()
        p = make_program(model)
        done_flag = threading.Event()

        def runner() -> None:
            p.run()
            done_flag.set()

        t = threading.Thread(target=runner, daemon=True)
        t.start()
        p.wait()
        assert done_flag.is_set()
        t.join()


class TestProgramFilter:
    def test_filter_discards_messages(self):
        """A filter returning None should prevent the message reaching update()."""
        model = FilterTestModel()

        discarded: list[tea.Msg] = []

        def my_filter(m: tea.Model, msg: tea.Msg) -> Optional[tea.Msg]:
            if isinstance(msg, tea.QuitMsg):
                discarded.append(msg)
                return None  # discard QuitMsg
            return msg

        p = make_program(model, filter=my_filter)

        # Since filter discards QuitMsg, we need another way out
        def killer() -> None:
            time.sleep(0.1)
            p.kill()

        t = threading.Thread(target=killer, daemon=True)
        t.start()

        try:
            p.run()
        except tea.ErrProgramKilled:
            pass
        t.join()

        # QuitMsg was discarded by the filter
        assert len(discarded) > 0

    def test_filter_transforms_messages(self):
        """A filter can replace one message with another."""
        received: list[tea.Msg] = []

        class TransformModel(tea.Model):
            def init(self):
                return tea.quit_cmd

            def update(self, msg):
                received.append(msg)
                return self, None

            def view(self):
                return ""

        def swap_filter(m: tea.Model, msg: tea.Msg) -> Optional[tea.Msg]:
            if isinstance(msg, tea.QuitMsg):
                return tea.KeyMsg(key="swapped")
            return msg

        model = TransformModel()
        p = make_program(model, filter=swap_filter)

        def killer():
            time.sleep(0.15)
            p.kill()

        t = threading.Thread(target=killer, daemon=True)
        t.start()
        try:
            p.run()
        except tea.ErrProgramKilled:
            pass
        t.join()

        assert any(isinstance(m, tea.KeyMsg) and m.key == "swapped" for m in received)


class TestNullRendererOption:
    def test_use_null_renderer_swaps_renderer(self):
        model = QuitOnFirstMsg()
        p = make_program(model)  # make_program already sets use_null_renderer=True
        assert isinstance(p._renderer, NullRenderer)


class TestStopEvent:
    def test_stop_event_exits_program(self):
        """Setting stop_event should cause the program to exit gracefully."""
        model = SenderModel()
        stop = threading.Event()
        p = make_program(model, stop_event=stop)

        def driver() -> None:
            time.sleep(0.05)
            stop.set()

        t = threading.Thread(target=driver, daemon=True)
        t.start()
        final = p.run()  # should return without raising
        assert final is model
        t.join()
