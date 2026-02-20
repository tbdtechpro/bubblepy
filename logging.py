"""Debug logging utilities for Bubble Tea programs.

Since the TUI occupies stdout and stderr, using print() or writing to
those streams corrupts the display.  Use log_to_file() to redirect log
output to a file and inspect it in a separate terminal with ``tail -f``.

Equivalent to Go's logging.go helpers.
"""

import logging


def log_to_file(path: str, prefix: str = "") -> logging.FileHandler:
    """Configure Python's logging module to write to a file.

    Opens (or appends to) *path* and attaches a FileHandler to the root
    logger (or to the named logger if *prefix* is given).  The handler is
    set to DEBUG level so all messages are captured.

    Args:
        path: Path to the log file.  Created if it does not exist; existing
              files are appended to (mode ``"a"``).
        prefix: Logger name.  If empty, the root logger is used; otherwise
                ``logging.getLogger(prefix)`` is configured.  Using a named
                logger avoids capturing log output from third-party libraries
                that also write to the root logger.

    Returns:
        The FileHandler that was attached.  Call ``handler.close()`` (or
        use it as a context manager) when the program exits to flush and
        release the file.

    Example::

        import bubbletea as tea

        fh = tea.log_to_file("debug.log", "myapp")
        # In a second terminal: tail -f debug.log
        ...
        p.run()
        fh.close()

    Equivalent to Go's ``tea.LogToFile("debug.log", "debug")``.
    """
    handler = logging.FileHandler(path, mode="a")
    if prefix:
        fmt = f"%(asctime)s {prefix} %(levelname)-8s %(message)s"
    else:
        fmt = "%(asctime)s %(levelname)-8s %(message)s"
    handler.setFormatter(logging.Formatter(fmt))
    handler.setLevel(logging.DEBUG)

    logger = logging.getLogger(prefix if prefix else None)
    logger.addHandler(handler)
    if logger.level == logging.NOTSET:
        logger.setLevel(logging.DEBUG)

    return handler
