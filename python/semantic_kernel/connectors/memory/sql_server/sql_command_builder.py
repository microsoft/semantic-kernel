# Copyright (c) Microsoft. All rights reserved.

from collections.abc import Sequence
from contextlib import contextmanager
from io import StringIO
from typing import Any

from semantic_kernel.connectors.memory import logger
from semantic_kernel.exceptions.vector_store_exceptions import VectorStoreOperationException


class QueryBuilder:
    """A class that helps you build strings for SQL queries."""

    def __init__(self, initial_string: "QueryBuilder | str | None" = None):
        """Initialize the StringBuilder with an empty StringIO object."""
        self._file_str = StringIO()
        if initial_string:
            self._file_str.write(str(initial_string))

    def append(self, string: str, suffix: str = ""):
        """Append a string to the StringBuilder."""
        self._file_str.write(string)
        if suffix:
            self._file_str.write(suffix)

    def append_list(self, strings: Sequence[str], sep: str = ", ", end: str = "\n"):
        """Append a list of strings to the StringBuilder with a separator and an end string."""
        for string in strings[:-1]:
            self.append(string, suffix=sep)
        self.append(strings[-1], suffix=end)

    def append_table_name(
        self, schema: str, table_name: str, prefix: str = "", suffix: str = "", newline: bool = False
    ) -> None:
        """Append a table name to the StringBuilder with schema.

        This includes square brackets around the schema and table name.
        And spaces around the table name.

        Args:
            schema: The schema name.
            table_name: The table name.
            prefix: Optional prefix to add before the table name.
            suffix: Optional suffix to add after the table name.
            newline: Whether to add a newline after the table name or suffix.
        """
        self.append(f"{prefix} [{schema}].[{table_name}] {suffix}", suffix="\n" if newline else "")

    def remove_last(self, number_of_chars: int):
        """Remove the last number_of_chars from the StringBuilder."""
        current_pos = self._file_str.tell()
        if current_pos >= number_of_chars:
            self._file_str.seek(current_pos - number_of_chars)
            self._file_str.truncate()

    @contextmanager
    def in_parenthesis(self, prefix: str = "", suffix: str = ""):
        """Context manager to add parentheses around a block of strings.

        Args:
            prefix: Optional prefix to add before the opening parenthesis.
            suffix: Optional suffix to add after the closing parenthesis.

        """
        self.append(f"{prefix} (" if prefix else "(")
        yield
        self.append(f") {suffix}" if suffix else ")")

    @contextmanager
    def in_logical_group(self):
        """Create a logical group with BEGIN and END."""
        self.append("BEGIN", suffix="\n")
        yield
        self.append("END", suffix="\n")

    def __str__(self):
        """Return the string representation of the StringBuilder."""
        return self._file_str.getvalue()


class SqlCommand:
    """A class that represents a SQL command."""

    def __init__(
        self,
        query: QueryBuilder | str | None = None,
        execute_many: bool = False,
    ):
        """Initialize the SqlCommand.

        This only allows for creation of the query string, use the add_parameter
        and add_parameters methods to add parameters to the command.

        Args:
            query: The SQL command string or QueryBuilder object.
            execute_many: Whether to execute the command many times.
                If True, the parameters will be added to each of the many_parameters contents.
                If False, the parameters will be added to the parameters list.

        """
        self.query = QueryBuilder(query)
        self.parameters: list[str] = []
        self.many_parameters: list[tuple[str, ...]] = []
        self.execute_many: bool = execute_many

    def add_parameter(self, value: str) -> None:
        """Add a parameter to the SqlCommand.

        This adds a single value to the parameters.
        If the command is set to execute many, it will add the parameters
        to each of the the many_parameters contents.
        """
        if self.execute_many:
            for i in range(len(self.many_parameters)):
                self.many_parameters[i] += (value,)
        else:
            if (len(self.parameters) + 1) > 2100:
                raise VectorStoreOperationException("The maximum number of parameters is 2100.")
            self.parameters.append(value)

    def add_parameters(self, values: Sequence[str] | tuple[str, ...]) -> None:
        """Add multiple parameters to the SqlCommand.

        If the command is set to execute many, it will add a single new tuple to the many_parameters attribute.
        If the command is not set to execute many, it will add the values to the parameters list.
        """
        if self.execute_many:
            self.many_parameters.append(tuple(values))
        else:
            if (len(self.parameters) + len(values)) > 2100:
                raise VectorStoreOperationException("The maximum number of parameters is 2100.")
            self.parameters.extend(values)

    def __str__(self):
        """Return the string representation of the SqlCommand."""
        if self.parameters:
            logger.debug("This command has parameters.")
        return str(self.query)

    def to_execute(self) -> tuple[str, tuple[Any, ...]]:
        """Return the command and parameters for execute or execute many."""
        if self.execute_many:
            return str(self.query), tuple(self.many_parameters)
        return str(self.query), tuple(self.parameters)
