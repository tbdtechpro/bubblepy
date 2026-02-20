#!/usr/bin/env python3
"""Fetch a URL in the background and display the result.

Port of examples/http/main.go.

Demonstrates using a Cmd that performs I/O (an HTTP GET) and delivers its
result as a message to update().

Run:
    python examples/http.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

import urllib.request
import urllib.error
from dataclasses import dataclass
from typing import Optional

import bubbletea as tea


URL = "https://charm.sh"


@dataclass
class GotResponseMsg:
    status_code: int
    content_length: int


@dataclass
class ErrMsg:
    error: Exception


class HttpModel(tea.Model):
    def __init__(self) -> None:
        self.status: Optional[int] = None
        self.content_length: Optional[int] = None
        self.error: Optional[str] = None
        self.loading = True

    def init(self) -> Optional[tea.Cmd]:
        return fetch_url(URL)

    def update(self, msg: tea.Msg):
        if isinstance(msg, tea.KeyMsg):
            if msg.key in ("ctrl+c", "q"):
                return self, tea.quit_cmd

        if isinstance(msg, GotResponseMsg):
            self.loading = False
            self.status = msg.status_code
            self.content_length = msg.content_length
            return self, None

        if isinstance(msg, ErrMsg):
            self.loading = False
            self.error = str(msg.error)
            return self, None

        return self, None

    def view(self) -> str:
        if self.loading:
            return f"Fetching {URL}...\n"
        if self.error:
            return f"Error: {self.error}\n\nPress q to quit.\n"
        return (
            f"Got a response from {URL}!\n\n"
            f"  Status:         {self.status}\n"
            f"  Content-Length: {self.content_length}\n\n"
            "Press q to quit.\n"
        )


def fetch_url(url: str) -> tea.Cmd:
    """Return a Cmd that fetches url and delivers the result as a message."""
    def cmd() -> tea.Msg:
        try:
            with urllib.request.urlopen(url, timeout=10) as resp:
                return GotResponseMsg(
                    status_code=resp.status,
                    content_length=int(resp.headers.get("Content-Length", -1)),
                )
        except Exception as exc:
            return ErrMsg(error=exc)

    return cmd


if __name__ == "__main__":
    p = tea.Program(HttpModel())
    try:
        p.run()
    except tea.ErrInterrupted:
        pass
