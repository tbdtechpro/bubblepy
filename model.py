"""Model protocol for Bubble Tea applications."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional, Tuple

if TYPE_CHECKING:
    from .commands import Cmd
    from .messages import Msg


class Model(ABC):
    """
    Abstract base class for Bubble Tea models.

    A Model represents the state of your application. You must implement
    three methods:

    - init(): Returns an optional initial command
    - update(msg): Handles messages and returns updated model + optional command
    - view(): Returns a string representation of the UI
    """

    @abstractmethod
    def init(self) -> Optional["Cmd"]:
        """
        Initialize the model. Called once when the program starts.

        Returns an optional Cmd to perform initial I/O.
        Return None for no initial command.
        """
        pass

    @abstractmethod
    def update(self, msg: "Msg") -> Tuple["Model", Optional["Cmd"]]:
        """
        Update the model based on a message.

        Args:
            msg: The message to process

        Returns:
            A tuple of (updated_model, optional_command)
        """
        pass

    @abstractmethod
    def view(self) -> str:
        """
        Render the model as a string for display.

        The returned string must end with a trailing newline (``\n``).
        The renderer counts newlines to determine how many lines to erase
        on the next frame; omitting the trailing newline causes the count
        to be off by one, making the UI drift down by one line per redraw.
        The renderer auto-corrects a missing trailing newline, but relying
        on this is not recommended.

        Example::

            def view(self) -> str:
                return f"Counter: {self.count}\n"

        Returns:
            A string representation of the current UI state, ending with ``\n``.
        """
        pass
