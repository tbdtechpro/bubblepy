"""Mouse handling for Bubble Tea."""

from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional


class MouseButton(Enum):
    """Mouse button types."""

    NONE = auto()
    LEFT = auto()
    MIDDLE = auto()
    RIGHT = auto()
    WHEEL_UP = auto()
    WHEEL_DOWN = auto()
    WHEEL_LEFT = auto()
    WHEEL_RIGHT = auto()
    BUTTON_4 = auto()
    BUTTON_5 = auto()


class MouseAction(Enum):
    """Mouse action types."""

    PRESS = auto()
    RELEASE = auto()
    MOTION = auto()


@dataclass
class MouseEvent:
    """Represents a mouse event."""

    x: int
    y: int
    button: MouseButton
    action: MouseAction
    alt: bool = False
    ctrl: bool = False
    shift: bool = False


def parse_mouse_event(data: bytes) -> Optional[MouseEvent]:
    """Parse a mouse event from raw terminal bytes.

    Supports two wire protocols:

    * **SGR** (``ESC [ < Cb ; Cx ; Cy M/m``) -- preferred; unlimited
      coordinate range, distinguishes press from release.
    * **X10 legacy** (``ESC [ M <cb> <cx> <cy>``) -- three raw bytes after
      the prefix, each value = position/button + 0x20.  Maximum coordinate
      is 223.  Falls back automatically when the terminal does not support SGR.

    Returns ``None`` if *data* does not match either protocol.
    """
    try:
        # X10 legacy protocol: ESC [ M <cb> <cx> <cy>  (exactly 6 bytes)
        # Must be checked before SGR since both start with ESC [ M / ESC [ <.
        if len(data) >= 6 and data[:3] == b"\x1b[M":
            cb = data[3] - 0x20
            cx = max(0, data[4] - 0x21)  # 1-based + 0x20 offset -> 0-based
            cy = max(0, data[5] - 0x21)

            shift = bool(cb & 4)
            alt = bool(cb & 8)
            ctrl = bool(cb & 16)
            btn = cb & 3

            if btn == 3:
                # X10 uses button=3 to signal release (no 'm' terminator)
                return MouseEvent(
                    x=cx,
                    y=cy,
                    button=MouseButton.NONE,
                    action=MouseAction.RELEASE,
                    alt=alt,
                    ctrl=ctrl,
                    shift=shift,
                )

            button = (
                MouseButton.LEFT
                if btn == 0
                else MouseButton.MIDDLE if btn == 1 else MouseButton.RIGHT
            )
            return MouseEvent(
                x=cx,
                y=cy,
                button=button,
                action=MouseAction.PRESS,
                alt=alt,
                ctrl=ctrl,
                shift=shift,
            )

        text = data.decode("utf-8", errors="ignore")

        # SGR extended mouse mode: ESC [ < Cb ; Cx ; Cy M/m
        if text.startswith("\x1b[<"):
            # Remove prefix and find terminator
            rest = text[3:]

            if "M" in rest:
                parts, _ = rest.split("M", 1)
                is_release = False
            elif "m" in rest:
                parts, _ = rest.split("m", 1)
                is_release = True
            else:
                return None

            nums = parts.split(";")
            if len(nums) != 3:
                return None

            cb = int(nums[0])
            cx = int(nums[1]) - 1  # Convert to 0-based
            cy = int(nums[2]) - 1  # Convert to 0-based

            # Parse modifiers
            shift = bool(cb & 4)
            alt = bool(cb & 8)
            ctrl = bool(cb & 16)

            # Parse button
            motion = bool(cb & 32)
            button_num = cb & 3

            # Wheel events
            if cb & 64:
                if button_num == 0:
                    button = MouseButton.WHEEL_UP
                elif button_num == 1:
                    button = MouseButton.WHEEL_DOWN
                elif button_num == 2:
                    button = MouseButton.WHEEL_LEFT
                else:
                    button = MouseButton.WHEEL_RIGHT
                action = MouseAction.PRESS
            else:
                # Regular buttons
                if button_num == 0:
                    button = MouseButton.LEFT
                elif button_num == 1:
                    button = MouseButton.MIDDLE
                elif button_num == 2:
                    button = MouseButton.RIGHT
                else:
                    button = MouseButton.NONE

                if motion:
                    action = MouseAction.MOTION
                elif is_release:
                    action = MouseAction.RELEASE
                else:
                    action = MouseAction.PRESS

            return MouseEvent(
                x=cx,
                y=cy,
                button=button,
                action=action,
                alt=alt,
                ctrl=ctrl,
                shift=shift,
            )
    except (ValueError, IndexError):
        pass

    return None
