# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

import json
from typing import Any

from semantic_kernel.exceptions import FunctionCallInvalidArgumentsException, FunctionCallInvalidNameException
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel_pydantic import KernelBaseModel


class FunctionCall(KernelBaseModel):
    """Class to hold a function call response."""

    name: str | None = None
    arguments: str | None = None

    def __add__(self, other: "FunctionCall | None") -> "FunctionCall":
        """Add two function calls together, combines the arguments, ignores the name."""
        if not other:
            return self
        return FunctionCall(name=self.name or other.name, arguments=(self.arguments or "") + (other.arguments or ""))

    def parse_arguments(self) -> dict[str, Any] | None:
        """Parse the arguments into a dictionary."""
        if not self.arguments:
            return None
        try:
            return json.loads(self.arguments)
        except json.JSONDecodeError as exc:
            raise FunctionCallInvalidArgumentsException("Function Call arguments are not valid JSON.") from exc

    def to_kernel_arguments(self) -> KernelArguments:
        """Return the arguments as a KernelArguments instance."""
        args = self.parse_arguments()
        if not args:
            return KernelArguments()
        return KernelArguments(**args)

    def split_name(self) -> list[str]:
        """Split the name into a plugin and function name."""
        if not self.name:
            raise FunctionCallInvalidNameException("Name is not set.")
        if "-" not in self.name:
            return ["", self.name]
        return self.name.split("-", maxsplit=1)

    def split_name_dict(self) -> dict[str, str]:
        """Split the name into a plugin and function name."""
        parts = self.split_name()
        return {"plugin_name": parts[0], "function_name": parts[1]}
