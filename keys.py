"""Key handling for Bubble Tea."""

from enum import Enum, auto
from typing import Optional


class KeyType(Enum):
    """Special key types."""

    # Navigation
    UP = auto()
    DOWN = auto()
    LEFT = auto()
    RIGHT = auto()
    HOME = auto()
    END = auto()
    PAGE_UP = auto()
    PAGE_DOWN = auto()

    # Editing
    BACKSPACE = auto()
    DELETE = auto()
    INSERT = auto()
    TAB = auto()
    SHIFT_TAB = auto()
    ENTER = auto()
    ESCAPE = auto()
    SPACE = auto()

    # Function keys
    F1 = auto()
    F2 = auto()
    F3 = auto()
    F4 = auto()
    F5 = auto()
    F6 = auto()
    F7 = auto()
    F8 = auto()
    F9 = auto()
    F10 = auto()
    F11 = auto()
    F12 = auto()

    # Control characters
    CTRL_A = auto()
    CTRL_B = auto()
    CTRL_C = auto()
    CTRL_D = auto()
    CTRL_E = auto()
    CTRL_F = auto()
    CTRL_G = auto()
    CTRL_H = auto()
    CTRL_I = auto()
    CTRL_J = auto()
    CTRL_K = auto()
    CTRL_L = auto()
    CTRL_M = auto()
    CTRL_N = auto()
    CTRL_O = auto()
    CTRL_P = auto()
    CTRL_Q = auto()
    CTRL_R = auto()
    CTRL_S = auto()
    CTRL_T = auto()
    CTRL_U = auto()
    CTRL_V = auto()
    CTRL_W = auto()
    CTRL_X = auto()
    CTRL_Y = auto()
    CTRL_Z = auto()

    # Misc
    NULL = auto()
    RUNE = auto()  # Regular character


# Mapping of escape sequences to key names
ESCAPE_SEQUENCES = {
    # Arrow keys
    "\x1b[A": "up",
    "\x1b[B": "down",
    "\x1b[C": "right",
    "\x1b[D": "left",
    "\x1bOA": "up",
    "\x1bOB": "down",
    "\x1bOC": "right",
    "\x1bOD": "left",
    # Navigation
    "\x1b[H": "home",
    "\x1b[F": "end",
    "\x1b[1~": "home",
    "\x1b[4~": "end",
    "\x1b[5~": "pgup",
    "\x1b[6~": "pgdown",
    "\x1b[2~": "insert",
    "\x1b[3~": "delete",
    # Function keys
    "\x1bOP": "f1",
    "\x1bOQ": "f2",
    "\x1bOR": "f3",
    "\x1bOS": "f4",
    "\x1b[15~": "f5",
    "\x1b[17~": "f6",
    "\x1b[18~": "f7",
    "\x1b[19~": "f8",
    "\x1b[20~": "f9",
    "\x1b[21~": "f10",
    "\x1b[23~": "f11",
    "\x1b[24~": "f12",
    # Special
    "\x1b[Z": "shift+tab",
}

# Control character mappings
CTRL_KEYS = {
    0: "ctrl+@",
    1: "ctrl+a",
    2: "ctrl+b",
    3: "ctrl+c",
    4: "ctrl+d",
    5: "ctrl+e",
    6: "ctrl+f",
    7: "ctrl+g",
    8: "backspace",  # ctrl+h
    9: "tab",  # ctrl+i
    10: "enter",  # ctrl+j (newline)
    11: "ctrl+k",
    12: "ctrl+l",
    13: "enter",  # ctrl+m (carriage return)
    14: "ctrl+n",
    15: "ctrl+o",
    16: "ctrl+p",
    17: "ctrl+q",
    18: "ctrl+r",
    19: "ctrl+s",
    20: "ctrl+t",
    21: "ctrl+u",
    22: "ctrl+v",
    23: "ctrl+w",
    24: "ctrl+x",
    25: "ctrl+y",
    26: "ctrl+z",
    27: "escape",  # ctrl+[
    28: "ctrl+\\",
    29: "ctrl+]",
    30: "ctrl+^",
    31: "ctrl+_",
    127: "backspace",
}


class Key:
    """Represents a key press."""

    def __init__(self, char: str = "", key_type: Optional[KeyType] = None, alt: bool = False):
        self.char = char
        self.type = key_type or KeyType.RUNE
        self.alt = alt

    def __str__(self) -> str:
        prefix = "alt+" if self.alt else ""
        if self.type == KeyType.RUNE:
            return f"{prefix}{self.char}"
        return f"{prefix}{self.type.name.lower()}"


def parse_key(data: bytes) -> Optional[str]:
    """
    Parse raw input bytes into a key string.

    Returns the key name (e.g., "a", "enter", "ctrl+c", "up")
    """
    if not data:
        return None

    text = data.decode("utf-8", errors="ignore")

    # Check for escape sequences first
    if text.startswith("\x1b"):
        # Check for alt+key (escape followed by single char)
        if len(text) == 2 and text[1].isprintable():
            return f"alt+{text[1]}"

        # Check known escape sequences
        for seq, name in ESCAPE_SEQUENCES.items():
            if text.startswith(seq):
                return name

        # Just escape
        if len(text) == 1:
            return "escape"

        return None

    # Check for control characters
    if len(text) == 1:
        code = ord(text)
        if code in CTRL_KEYS:
            return CTRL_KEYS[code]

        # Space
        if code == 32:
            return " "

        # Regular printable character
        if text.isprintable():
            return text

    # Multi-byte UTF-8 character
    if len(text) == 1 or (len(data) > 1 and text):
        return text[0] if text else None

    return None
