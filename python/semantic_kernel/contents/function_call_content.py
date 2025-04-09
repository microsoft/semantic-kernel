# Copyright (c) Microsoft. All rights reserved.

import json
import logging
import re
from collections.abc import Mapping
from typing import TYPE_CHECKING, Any, ClassVar, Final, Literal, TypeVar
from xml.etree.ElementTree import Element  # nosec

from pydantic import Field
from typing_extensions import deprecated

from semantic_kernel.const import DEFAULT_FULLY_QUALIFIED_NAME_SEPARATOR
from semantic_kernel.contents.const import FUNCTION_CALL_CONTENT_TAG, ContentTypes
from semantic_kernel.contents.kernel_content import KernelContent
from semantic_kernel.exceptions import (
    ContentAdditionException,
    ContentInitializationError,
    FunctionCallInvalidArgumentsException,
    FunctionCallInvalidNameException,
)

if TYPE_CHECKING:
    from semantic_kernel.functions.kernel_arguments import KernelArguments

logger = logging.getLogger(__name__)


_T = TypeVar("_T", bound="FunctionCallContent")

EMPTY_VALUES: Final[list[str | None]] = ["", "{}", None]


class FunctionCallContent(KernelContent):
    """Class to hold a function call response."""

    content_type: Literal[ContentTypes.FUNCTION_CALL_CONTENT] = Field(FUNCTION_CALL_CONTENT_TAG, init=False)  # type: ignore
    tag: ClassVar[str] = FUNCTION_CALL_CONTENT_TAG
    id: str | None
    call_id: str | None = None
    index: int | None = None
    name: str | None = None
    function_name: str
    plugin_name: str | None = None
    arguments: str | Mapping[str, Any] | None = None

    def __init__(
        self,
        inner_content: Any | None = None,
        ai_model_id: str | None = None,
        id: str | None = None,
        index: int | None = None,
        name: str | None = None,
        function_name: str | None = None,
        plugin_name: str | None = None,
        arguments: str | Mapping[str, Any] | None = None,
        metadata: dict[str, Any] | None = None,
        call_id: str | None = None,
        **kwargs: Any,
    ) -> None:
        """Create function call content.

        Args:
            inner_content (Any | None): The inner content.
            ai_model_id (str | None): The id of the AI model.
            id (str | None): The id of the function call.
            index (int | None): The index of the function call.
            name (str | None): The name of the function call.
                When not supplied function_name and plugin_name should be supplied.
            function_name (str | None): The function name.
                Not used when 'name' is supplied.
            plugin_name (str | None): The plugin name.
                Not used when 'name' is supplied.
            arguments (str | dict[str, Any] | None): The arguments of the function call.
            metadata (dict[str, Any] | None): The metadata of the function call.
            call_id (str | None): The id of the call.
            kwargs (Any): Additional arguments.
        """
        if function_name and plugin_name and not name:
            name = f"{plugin_name}{DEFAULT_FULLY_QUALIFIED_NAME_SEPARATOR}{function_name}"
        if name and not function_name and not plugin_name:
            if DEFAULT_FULLY_QUALIFIED_NAME_SEPARATOR in name:
                plugin_name, function_name = name.split(DEFAULT_FULLY_QUALIFIED_NAME_SEPARATOR, maxsplit=1)
            else:
                function_name = name
        args = {
            "inner_content": inner_content,
            "ai_model_id": ai_model_id,
            "id": id,
            "call_id": call_id,
            "index": index,
            "name": name,
            "function_name": function_name or "",
            "plugin_name": plugin_name,
            "arguments": arguments,
        }
        if metadata:
            args["metadata"] = metadata

        super().__init__(**args)

    def __str__(self) -> str:
        """Return the function call as a string."""
        if isinstance(self.arguments, dict):
            return f"{self.name}({json.dumps(self.arguments)})"
        return f"{self.name}({self.arguments})"

    def __add__(self, other: "FunctionCallContent | None") -> "FunctionCallContent":
        """Add two function calls together, combines the arguments, ignores the name.

        When both function calls have a dict as arguments, the arguments are merged,
        which means that the arguments of the second function call
        will overwrite the arguments of the first function call if the same key is present.

        When one of the two arguments are a dict and the other a string, we raise a ContentAdditionException.
        """
        if not other:
            return self
        if self.id and other.id and self.id != other.id:
            raise ContentAdditionException("Function calls have different ids.")
        if self.index != other.index:
            raise ContentAdditionException("Function calls have different indexes.")
        if self.call_id and other.call_id and self.call_id != other.call_id:
            raise ContentAdditionException("Function calls have different call ids.")
        return FunctionCallContent(
            id=self.id or other.id,
            call_id=self.call_id or other.call_id,
            index=self.index or other.index,
            name=self.name or other.name,
            arguments=self.combine_arguments(self.arguments, other.arguments),
            metadata=self.metadata | other.metadata,
        )

    def combine_arguments(
        self, arg1: str | Mapping[str, Any] | None, arg2: str | Mapping[str, Any] | None
    ) -> str | Mapping[str, Any]:
        """Combine two arguments."""
        if isinstance(arg1, Mapping) and isinstance(arg2, Mapping):
            return {**arg1, **arg2}
        # when one of the two is a dict, and the other isn't, we raise.
        if isinstance(arg1, Mapping) or isinstance(arg2, Mapping):
            raise ContentAdditionException("Cannot combine a dict with a string.")
        if arg1 in EMPTY_VALUES and arg2 in EMPTY_VALUES:
            return "{}"
        if arg1 in EMPTY_VALUES:
            return arg2 or "{}"
        if arg2 in EMPTY_VALUES:
            return arg1 or "{}"
        return (arg1 or "") + (arg2 or "")

    def parse_arguments(self) -> Mapping[str, Any] | None:
        """Parse the arguments into a dictionary."""
        if not self.arguments:
            return None
        if isinstance(self.arguments, Mapping):
            return self.arguments
        try:
            return json.loads(self.arguments)
        except json.JSONDecodeError as exc:
            logger.debug("Function Call arguments are not valid JSON. Trying to preprocess.")
            try:
                # Python strings can be single quoted, but JSON strings should be double quoted.
                # JSON keys and values should be enclosed in double quotes.
                # Replace single quotes with double quotes, but not if it's an escaped single quote.
                return json.loads(re.sub(r"(?<!\\)'", '"', self.arguments).replace("\\'", "'"))
            except json.JSONDecodeError:
                raise FunctionCallInvalidArgumentsException(
                    "Function Call arguments are not valid JSON even after preprocessing."
                ) from exc

    def to_kernel_arguments(self) -> "KernelArguments":
        """Return the arguments as a KernelArguments instance."""
        from semantic_kernel.functions.kernel_arguments import KernelArguments

        args = self.parse_arguments()
        if not args:
            return KernelArguments()
        return KernelArguments(**args)

    @deprecated("The function_name and plugin_name properties should be used instead.")
    def split_name(self) -> list[str | None]:
        """Split the name into a plugin and function name."""
        if not self.function_name:
            raise FunctionCallInvalidNameException("Function name is not set.")
        return [self.plugin_name or "", self.function_name]

    @deprecated("The function_name and plugin_name properties should be used instead.")
    def split_name_dict(self) -> dict:
        """Split the name into a plugin and function name."""
        return {"plugin_name": self.plugin_name, "function_name": self.function_name}

    def custom_fully_qualified_name(self, separator: str) -> str:
        """Get the fully qualified name of the function with a custom separator.

        Args:
            separator (str): The custom separator.

        Returns:
            The fully qualified name of the function with a custom separator.
        """
        return f"{self.plugin_name}{separator}{self.function_name}" if self.plugin_name else self.function_name

    def to_element(self) -> Element:
        """Convert the function call to an Element."""
        element = Element(self.tag)
        if self.id:
            element.set("id", self.id)
        if self.name:
            element.set("name", self.name)
        if self.arguments:
            element.text = json.dumps(self.arguments) if isinstance(self.arguments, Mapping) else self.arguments
        return element

    @classmethod
    def from_element(cls: type[_T], element: Element) -> _T:
        """Create an instance from an Element."""
        if element.tag != cls.tag:
            raise ContentInitializationError(f"Element tag is not {cls.tag}")  # pragma: no cover

        return cls(name=element.get("name"), id=element.get("id"), arguments=element.text or "")

    def to_dict(self) -> dict[str, str | Any]:
        """Convert the instance to a dictionary."""
        args = json.dumps(self.arguments) if isinstance(self.arguments, Mapping) else self.arguments
        return {"id": self.id, "type": "function", "function": {"name": self.name, "arguments": args}}

    def __hash__(self) -> int:
        """Return the hash of the function call content."""
        args_hashable = frozenset(self.arguments.items()) if isinstance(self.arguments, Mapping) else None
        return hash((
            self.tag,
            self.id,
            self.call_id,
            self.index,
            self.name,
            self.function_name,
            self.plugin_name,
            args_hashable,
        ))
