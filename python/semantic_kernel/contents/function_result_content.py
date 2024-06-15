# Copyright (c) Microsoft. All rights reserved.

from functools import cached_property
from typing import TYPE_CHECKING, Any
from xml.etree.ElementTree import Element  # nosec

from pydantic import field_validator

from semantic_kernel.contents.author_role import AuthorRole
from semantic_kernel.contents.const import FUNCTION_RESULT_CONTENT_TAG, TEXT_CONTENT_TAG
from semantic_kernel.contents.kernel_content import KernelContent
from semantic_kernel.contents.text_content import TextContent

if TYPE_CHECKING:
    from semantic_kernel.contents.chat_message_content import ChatMessageContent
    from semantic_kernel.contents.function_call_content import FunctionCallContent
    from semantic_kernel.functions.function_result import FunctionResult

TAG_CONTENT_MAP = {
    TEXT_CONTENT_TAG: TextContent,
}


class FunctionResultContent(KernelContent):
    """This is the base class for text response content.

    All Text Completion Services should return an instance of this class as response.
    Or they can implement their own subclass of this class and return an instance.

    Args:
        inner_content: Any - The inner content of the response,
            this should hold all the information from the response so even
            when not creating a subclass a developer can leverage the full thing.
        ai_model_id: str | None - The id of the AI model that generated this response.
        metadata: dict[str, Any] - Any metadata that should be attached to the response.
        text: str | None - The text of the response.
        encoding: str | None - The encoding of the text.

    Methods:
        __str__: Returns the text of the response.
    """

    id: str
    name: str | None = None
    result: str
    encoding: str | None = None

    @cached_property
    def function_name(self) -> str:
        """Get the function name."""
        return self.split_name()[1]

    @cached_property
    def plugin_name(self) -> str | None:
        """Get the plugin name."""
        return self.split_name()[0]

    @field_validator("result", mode="before")
    @classmethod
    def _validate_result(cls, result: Any):
        if not isinstance(result, str):
            result = str(result)
        return result

    def __str__(self) -> str:
        """Return the text of the response."""
        return self.result

    def to_element(self) -> Element:
        """Convert the instance to an Element."""
        element = Element(FUNCTION_RESULT_CONTENT_TAG)
        element.set("id", self.id)
        if self.name:
            element.set("name", self.name)
        element.text = str(self.result)
        return element

    @classmethod
    def from_element(cls, element: Element) -> "FunctionResultContent":
        """Create an instance from an Element."""
        if element.tag != FUNCTION_RESULT_CONTENT_TAG:
            raise ValueError(f"Element tag is not {FUNCTION_RESULT_CONTENT_TAG}")
        return cls(id=element.get("id", ""), result=element.text, name=element.get("name", None))  # type: ignore

    @classmethod
    def from_function_call_content_and_result(
        cls,
        function_call_content: "FunctionCallContent",
        result: "FunctionResult | TextContent | ChatMessageContent | Any",
        metadata: dict[str, Any] = {},
    ) -> "FunctionResultContent":
        """Create an instance from a FunctionCallContent and a result."""
        if function_call_content.metadata:
            metadata.update(function_call_content.metadata)
        return cls(
            id=function_call_content.id,
            result=result,  # type: ignore
            name=function_call_content.name,
            ai_model_id=function_call_content.ai_model_id,
            metadata=metadata,
        )

    def to_chat_message_content(self, unwrap: bool = False) -> "ChatMessageContent":
        """Convert the instance to a ChatMessageContent."""
        from semantic_kernel.contents.chat_message_content import ChatMessageContent

        if unwrap:
            return ChatMessageContent(role=AuthorRole.TOOL, items=[self.result])  # type: ignore
        return ChatMessageContent(role=AuthorRole.TOOL, items=[self])  # type: ignore

    def to_dict(self) -> dict[str, str]:
        """Convert the instance to a dictionary."""
        return {
            "tool_call_id": self.id,
            "content": self.result,
        }

    def split_name(self) -> list[str]:
        """Split the name into a plugin and function name."""
        if not self.name:
            raise ValueError("Name is not set.")
        if "-" not in self.name:
            return ["", self.name]
        return self.name.split("-", maxsplit=1)
