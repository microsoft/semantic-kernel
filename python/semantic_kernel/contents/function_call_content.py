# Copyright (c) Microsoft. All rights reserved.

import json
import logging
from functools import cached_property
from typing import TYPE_CHECKING, Any, ClassVar, Literal, TypeVar
from xml.etree.ElementTree import Element  # nosec

from pydantic import Field

from semantic_kernel.contents.const import FUNCTION_CALL_CONTENT_TAG, ContentTypes
from semantic_kernel.contents.kernel_content import KernelContent
from semantic_kernel.exceptions import FunctionCallInvalidArgumentsException, FunctionCallInvalidNameException
from semantic_kernel.exceptions.content_exceptions import ContentInitializationError

if TYPE_CHECKING:
    from semantic_kernel.functions.kernel_arguments import KernelArguments

logger = logging.getLogger(__name__)


_T = TypeVar("_T", bound="FunctionCallContent")


class FunctionCallContent(KernelContent):
    """Class to hold a function call response."""

    content_type: Literal[ContentTypes.FUNCTION_CALL_CONTENT] = Field(FUNCTION_CALL_CONTENT_TAG, init=False)  # type: ignore
    tag: ClassVar[str] = FUNCTION_CALL_CONTENT_TAG
    id: str | None
    index: int | None = None
    name: str | None = None
    arguments: str | None = None

    @cached_property
    def function_name(self) -> str:
        """Get the function name."""
        return self.split_name()[1]

    @cached_property
    def plugin_name(self) -> str | None:
        """Get the plugin name."""
        return self.split_name()[0]

    def __str__(self) -> str:
        """Return the function call as a string."""
        return f"{self.name}({self.arguments})"

    def __add__(self, other: "FunctionCallContent | None") -> "FunctionCallContent":
        """Add two function calls together, combines the arguments, ignores the name."""
        if not other:
            return self
        if self.id and other.id and self.id != other.id:
            raise ValueError("Function calls have different ids.")
        if self.index != other.index:
            raise ValueError("Function calls have different indexes.")
        return FunctionCallContent(
            id=self.id or other.id,
            index=self.index or other.index,
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
        element = Element(self.tag)
        if self.id:
            element.set("id", self.id)
        if self.name:
            element.set("name", self.name)
        if self.arguments:
            element.text = self.arguments
        return element

    @classmethod
    def from_element(cls: type[_T], element: Element) -> _T:
        """Create an instance from an Element."""
        if element.tag != cls.tag:
            raise ContentInitializationError(f"Element tag is not {cls.tag}")

        return cls(name=element.get("name"), id=element.get("id"), arguments=element.text or "")

    def to_dict(self) -> dict[str, str | Any]:
        """Convert the instance to a dictionary."""
        return {"id": self.id, "type": "function", "function": {"name": self.name, "arguments": self.arguments}}
