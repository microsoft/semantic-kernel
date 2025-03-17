# Copyright (c) Microsoft. All rights reserved.

from collections.abc import Iterable, MutableSequence, Sequence
from contextlib import contextmanager
from io import StringIO
from typing import Any


class StringBuilder:
    """A class that helps you build strings for SQL queries."""

    def __init__(self):
        """Initialize the StringBuilder with an empty StringIO object."""
        self._file_str = StringIO()

    def append(self, string: str):
        """Append a string to the StringBuilder."""
        self._file_str.write(string)

    def append_list(self, strings: Sequence[str], sep: str = ", ", end: str = "\n"):
        """Append a list of strings to the StringBuilder with a separator and an end string."""
        for string in strings[:-1]:
            self._file_str.write(string)
            self._file_str.write(sep)
        self._file_str.write(strings[-1])
        self._file_str.write(end)

    def append_with_newline(self, string: str):
        """Append a string to the StringBuilder followed by a newline."""
        self._file_str.write(string)
        self._file_str.write("\n")

    def append_newline(self) -> None:
        """Append a newline to the StringBuilder."""
        self._file_str.write("\n")

    def remove_last(self, number_of_chars: int):
        """Remove the last number_of_chars from the StringBuilder."""
        current_pos = self._file_str.tell()
        if current_pos >= number_of_chars:
            self._file_str.seek(current_pos - number_of_chars)
            self._file_str.truncate()

    @contextmanager
    def in_parenthesis(self, start: str = "", end: str = ""):
        """Context manager to add parentheses around a block of strings."""
        self.append(f"{start} (" if start else "(")
        yield
        self.append(f") {end}" if end else ")")

    @contextmanager
    def in_logical_group(self):
        """Create a logical group with BEGIN and END."""
        self.append_with_newline("BEGIN")
        yield
        self.append_with_newline("END")

    def __str__(self):
        """Return the string representation of the StringBuilder."""
        return self._file_str.getvalue()


class SqlCommand:
    """A class that represents a SQL command."""

    def __init__(
        self,
        command: StringBuilder | str | None = None,
        parameters: MutableSequence[str | tuple[str]] | None = None,
    ):
        """Initialize the SqlCommand with a command string."""
        if not command:
            self.command = StringBuilder()
        elif isinstance(command, str):
            self.command = StringBuilder()
            self.command.append(command)
        else:
            self.command = command
        self.parameters = parameters or []

    def add_parameter(self, value: str | tuple[str] | Sequence[str]) -> None:
        """Add a parameter to the SqlCommand."""
        match value:
            case str():
                self.parameters.append(value)
            case tuple():
                self.parameters.append(value)
            case Sequence():
                self.parameters.append(tuple(value))
            case _:
                raise TypeError(f"Unsupported parameter type: {type(value)}")

    def __str__(self):
        """Return the string representation of the SqlCommand."""
        return str(self.command)

    @property
    def is_execute_many(self) -> bool:
        """Check if the command is for executemany.

        This means there are strings in the parameters list
        and the first parameter is an iterable and there are at least 2 parameters.
        """
        return len(self.parameters) > 1 and isinstance(self.parameters[0], Iterable)

    def to_execute(self) -> tuple[str, tuple[Any]]:
        """Return the command and parameters for execute many.

        If there is only one parameter, it will be returned as a single value.
        """
        if self.is_execute_many and len(self.parameters) == 1:
            return str(self.command), tuple(self.parameters[0])
        return str(self.command), tuple(self.parameters)
