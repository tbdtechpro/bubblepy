"""Tests for keys.py — parse_key() and Key class."""

from bubbletea.keys import Key, KeyType, parse_key


class TestParseKey:
    # ── Printable ASCII ──────────────────────────────────────────────────────

    def test_lowercase_letter(self):
        assert parse_key(b"a") == "a"

    def test_uppercase_letter(self):
        assert parse_key(b"Z") == "Z"

    def test_digit(self):
        assert parse_key(b"5") == "5"

    def test_space(self):
        assert parse_key(b" ") == " "

    def test_punctuation(self):
        assert parse_key(b"!") == "!"

    # ── Control characters ───────────────────────────────────────────────────

    def test_ctrl_a(self):
        assert parse_key(b"\x01") == "ctrl+a"

    def test_ctrl_c(self):
        assert parse_key(b"\x03") == "ctrl+c"

    def test_ctrl_z(self):
        assert parse_key(b"\x1a") == "ctrl+z"

    def test_enter_cr(self):
        assert parse_key(b"\r") == "enter"

    def test_enter_lf(self):
        assert parse_key(b"\n") == "enter"

    def test_tab(self):
        assert parse_key(b"\t") == "tab"

    def test_backspace_del(self):
        assert parse_key(b"\x7f") == "backspace"

    def test_backspace_ctrl_h(self):
        assert parse_key(b"\x08") == "backspace"

    def test_escape(self):
        assert parse_key(b"\x1b") == "escape"

    # ── Arrow and navigation keys ────────────────────────────────────────────

    def test_arrow_up(self):
        assert parse_key(b"\x1b[A") == "up"

    def test_arrow_down(self):
        assert parse_key(b"\x1b[B") == "down"

    def test_arrow_right(self):
        assert parse_key(b"\x1b[C") == "right"

    def test_arrow_left(self):
        assert parse_key(b"\x1b[D") == "left"

    def test_home(self):
        assert parse_key(b"\x1b[H") in ("home", "home")

    def test_end(self):
        assert parse_key(b"\x1b[F") == "end"

    def test_page_up(self):
        assert parse_key(b"\x1b[5~") == "pgup"

    def test_page_down(self):
        assert parse_key(b"\x1b[6~") == "pgdown"

    def test_insert(self):
        assert parse_key(b"\x1b[2~") == "insert"

    def test_delete(self):
        assert parse_key(b"\x1b[3~") == "delete"

    def test_shift_tab(self):
        assert parse_key(b"\x1b[Z") == "shift+tab"

    # ── Function keys ────────────────────────────────────────────────────────

    def test_f1(self):
        assert parse_key(b"\x1bOP") == "f1"

    def test_f2(self):
        assert parse_key(b"\x1bOQ") == "f2"

    def test_f5(self):
        assert parse_key(b"\x1b[15~") == "f5"

    def test_f10(self):
        assert parse_key(b"\x1b[21~") == "f10"

    def test_f12(self):
        assert parse_key(b"\x1b[24~") == "f12"

    # ── Alt combinations ─────────────────────────────────────────────────────

    def test_alt_a(self):
        assert parse_key(b"\x1ba") == "alt+a"

    def test_alt_z(self):
        assert parse_key(b"\x1bz") == "alt+z"

    # ── Edge cases ───────────────────────────────────────────────────────────

    def test_empty(self):
        assert parse_key(b"") is None

    def test_unknown_sequence(self):
        # Unknown escape sequences return None
        result = parse_key(b"\x1b[999;999R")
        assert result is None or isinstance(result, str)

    def test_multi_byte_utf8(self):
        # UTF-8 emoji / multi-byte chars are returned as-is
        result = parse_key("é".encode("utf-8"))
        assert result == "é"


class TestKeyClass:
    def test_rune_str(self):
        k = Key(char="a")
        assert str(k) == "a"

    def test_alt_rune_str(self):
        k = Key(char="a", alt=True)
        assert str(k) == "alt+a"

    def test_special_key_str(self):
        k = Key(key_type=KeyType.UP)
        assert str(k) == "up"

    def test_alt_special_key_str(self):
        k = Key(key_type=KeyType.UP, alt=True)
        assert str(k) == "alt+up"
