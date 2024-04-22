# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

import json
import logging
from typing import TYPE_CHECKING, Any
from xml.etree.ElementTree import Element

from semantic_kernel.contents.const import FUNCTION_CALL_CONTENT_TAG
from semantic_kernel.contents.kernel_content import KernelContent
from semantic_kernel.exceptions import FunctionCallInvalidArgumentsException, FunctionCallInvalidNameException

if TYPE_CHECKING:
    from semantic_kernel.functions.kernel_arguments import KernelArguments

logger = logging.getLogger(__name__)


class FunctionCallContent(KernelContent):
    """Class to hold a function call response."""

    id: str | None
    name: str | None = None
    arguments: str | None = None

    def __str__(self) -> str:
        return f"{self.name}({self.arguments})"

    def __add__(self, other: "FunctionCallContent | None") -> "FunctionCallContent":
        """Add two function calls together, combines the arguments, ignores the name."""
        if not other:
            return self
        if self.id and other.id and self.id != other.id:
            raise ValueError("Function calls have different ids.")
        return FunctionCallContent(
            id=self.id or other.id,
            name=self.name or other.name,
            arguments=(self.arguments or "") + (other.arguments or ""),
        )

    def parse_arguments(self) -> dict[str, Any] | None:
        """Parse the arguments into a dictionary."""
        if not self.arguments:
            return None
        try:
            return json.loads(self.arguments)
        except json.JSONDecodeError as exc:
            raise FunctionCallInvalidArgumentsException("Function Call arguments are not valid JSON.") from exc

    def to_kernel_arguments(self) -> "KernelArguments":
        """Return the arguments as a KernelArguments instance."""
        from semantic_kernel.functions.kernel_arguments import KernelArguments

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

    def split_name_dict(self) -> dict:
        """Split the name into a plugin and function name."""
        parts = self.split_name()
        return {"plugin_name": parts[0], "function_name": parts[1]}

    def to_element(self) -> Element:
        """Convert the function call to an Element."""
        element = Element(FUNCTION_CALL_CONTENT_TAG)
        if self.id:
            element.set("id", self.id)
        if self.name:
            element.set("name", self.name)
        if self.arguments:
            element.text = self.arguments
        return element

    @classmethod
    def from_element(cls, element: Element) -> "FunctionCallContent":
        """Create an instance from an Element."""
        if element.tag != FUNCTION_CALL_CONTENT_TAG:
            raise ValueError(f"Element tag is not {FUNCTION_CALL_CONTENT_TAG}")

        return cls(name=element.get("name"), id=element.get("id"), arguments=element.text or "")

    def to_dict(self) -> dict[str, str | Any]:
        """Convert the instance to a dictionary."""
        return {"id": self.id, "type": "function", "function": {"name": self.name, "arguments": self.arguments}}
