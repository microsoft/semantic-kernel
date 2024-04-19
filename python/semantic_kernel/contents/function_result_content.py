# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

from typing import TYPE_CHECKING, Any
from xml.etree.ElementTree import Element

from pydantic import field_validator

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

    All Text Completion Services should return a instance of this class as response.
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
    result: TextContent
    encoding: str | None = None

    @field_validator("result", mode="before")
    def _validate_result(cls, result: "FunctionResult | TextContent | ChatMessageContent | Any") -> "TextContent":
        """Validate the supplied result."""
        from semantic_kernel.contents.chat_message_content import ChatMessageContent
        from semantic_kernel.functions.function_result import FunctionResult

        if isinstance(result, FunctionResult):
            result = result.value
        if isinstance(result, ChatMessageContent):
            for item in result.items:
                if isinstance(item, TextContent):
                    return item
                    break
        if isinstance(result, str):
            return TextContent(text=result, inner_content=result)
        if isinstance(result, TextContent):
            return result
        raise ValueError(f"Result is not a valid type, could not parse to one either, result was {result}")

    def __str__(self) -> str:
        return str(self.result)

    def to_element(self) -> Element:
        """Convert the instance to an Element."""
        element = Element(FUNCTION_RESULT_CONTENT_TAG)
        element.set("id", self.id)
        if self.name:
            element.set("name", self.name)
        element.append(self.result.to_element())
        return element

    @classmethod
    def from_element(cls, element: Element) -> "FunctionResultContent":
        """Create an instance from an Element."""
        if element.tag != FUNCTION_RESULT_CONTENT_TAG:
            raise ValueError(f"Element tag is not {FUNCTION_RESULT_CONTENT_TAG}")
        result_element = element[0]
        if result_element.tag in TAG_CONTENT_MAP:
            result = TAG_CONTENT_MAP[result_element.tag].from_element(result_element)
        else:
            raise ValueError(f"Element child tag is not in {TAG_CONTENT_MAP.keys()}")
        return cls(id=element["id"], result=result, name=element.get("name", None))  # type: ignore

    @classmethod
    def from_function_call_content_and_result(
        cls,
        function_call_content: "FunctionCallContent",
        result: "FunctionResult | TextContent | ChatMessageContent | Any",
        metadata: dict[str, Any] = {},
    ) -> "FunctionResultContent":
        """Create an instance from a FunctionCallContent and a result."""
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
            return ChatMessageContent(role="tool", items=[self.result])  # type: ignore
        return ChatMessageContent(role="tool", items=[self])  # type: ignore

    def to_dict(self) -> dict[str, Any]:
        """Convert the instance to a dictionary."""
        return {
            "tool_call_id": self.id,
            "content": self.result.to_dict(),
        }
