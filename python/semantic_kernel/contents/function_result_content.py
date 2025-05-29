# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING, Any, ClassVar, Literal, TypeVar
from xml.etree.ElementTree import Element  # nosec

from pydantic import Field, field_serializer
from typing_extensions import deprecated

from semantic_kernel.const import DEFAULT_FULLY_QUALIFIED_NAME_SEPARATOR
from semantic_kernel.contents.const import FUNCTION_RESULT_CONTENT_TAG, TEXT_CONTENT_TAG, ContentTypes
from semantic_kernel.contents.image_content import ImageContent
from semantic_kernel.contents.kernel_content import KernelContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.contents.utils.hashing import make_hashable
from semantic_kernel.exceptions.content_exceptions import ContentInitializationError

if TYPE_CHECKING:
    from semantic_kernel.contents.chat_message_content import ChatMessageContent
    from semantic_kernel.contents.function_call_content import FunctionCallContent
    from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
    from semantic_kernel.functions.function_result import FunctionResult

TAG_CONTENT_MAP = {
    TEXT_CONTENT_TAG: TextContent,
}

_T = TypeVar("_T", bound="FunctionResultContent")


class FunctionResultContent(KernelContent):
    """This class represents function result content."""

    content_type: Literal[ContentTypes.FUNCTION_RESULT_CONTENT] = Field(FUNCTION_RESULT_CONTENT_TAG, init=False)  # type: ignore
    tag: ClassVar[str] = FUNCTION_RESULT_CONTENT_TAG
    id: str
    call_id: str | None = None
    result: Any
    name: str | None = None
    function_name: str
    plugin_name: str | None = None
    encoding: str | None = None

    def __init__(
        self,
        inner_content: Any | None = None,
        ai_model_id: str | None = None,
        id: str | None = None,
        call_id: str | None = None,
        name: str | None = None,
        function_name: str | None = None,
        plugin_name: str | None = None,
        result: Any | None = None,
        encoding: str | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Create function result content.

        Args:
            inner_content (Any | None): The inner content.
            ai_model_id (str | None): The id of the AI model.
            id (str | None): The id of the function call that the result relates to.
            call_id (str | None): The call id of the function call from the Responses API.
            name (str | None): The name of the function.
                When not supplied function_name and plugin_name should be supplied.
            function_name (str | None): The function name.
                Not used when 'name' is supplied.
            plugin_name (str | None): The plugin name.
                Not used when 'name' is supplied.
            result (Any | None): The result of the function.
            encoding (str | None): The encoding of the result.
            metadata (dict[str, Any] | None): The metadata of the function call.
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
            "name": name,
            "function_name": function_name or "",
            "plugin_name": plugin_name,
            "result": result,
            "encoding": encoding,
        }
        if call_id:
            args["call_id"] = call_id
        if metadata:
            args["metadata"] = metadata

        super().__init__(**args)

    def __str__(self) -> str:
        """Return the text of the response."""
        return str(self.result)

    def to_element(self) -> Element:
        """Convert the instance to an Element."""
        element = Element(self.tag)
        element.set("id", self.id)
        if self.name:
            element.set("name", self.name)
        element.text = str(self.result)
        return element

    @classmethod
    def from_element(cls: type[_T], element: Element) -> _T:
        """Create an instance from an Element."""
        if element.tag != cls.tag:
            raise ContentInitializationError(f"Element tag is not {cls.tag}")  # pragma: no cover
        return cls(id=element.get("id", ""), result=element.text, name=element.get("name", None))

    @classmethod
    def from_function_call_content_and_result(
        cls: type[_T],
        function_call_content: "FunctionCallContent",
        result: "FunctionResult | TextContent | ChatMessageContent | Any",
        metadata: dict[str, Any] | None = None,
    ) -> _T:
        """Create an instance from a FunctionCallContent and a result."""
        from semantic_kernel.contents.chat_message_content import ChatMessageContent
        from semantic_kernel.functions.function_result import FunctionResult

        metadata = metadata or {}
        metadata = metadata | (function_call_content.metadata or {})
        metadata = metadata | getattr(result, "metadata", {})
        inner_content = result
        if isinstance(result, FunctionResult):
            result = result.value
        if isinstance(result, TextContent):
            res = result.text
        elif isinstance(result, ChatMessageContent):
            if isinstance(result.items[0], TextContent):
                res = result.items[0].text
            elif isinstance(result.items[0], ImageContent):
                res = result.items[0].data_uri
            elif isinstance(result.items[0], FunctionResultContent):
                res = result.items[0].result
            res = str(result)
        else:
            res = result
        return cls(
            id=function_call_content.id or "unknown",
            call_id=function_call_content.call_id if hasattr(function_call_content, "call_id") else None,
            inner_content=inner_content,
            result=res,
            function_name=function_call_content.function_name,
            plugin_name=function_call_content.plugin_name,
            ai_model_id=function_call_content.ai_model_id,
            metadata=metadata,
        )

    def to_chat_message_content(self) -> "ChatMessageContent":
        """Convert the instance to a ChatMessageContent."""
        from semantic_kernel.contents.chat_message_content import ChatMessageContent

        return ChatMessageContent(role=AuthorRole.TOOL, items=[self])

    def to_streaming_chat_message_content(self) -> "StreamingChatMessageContent":
        """Convert the instance to a StreamingChatMessageContent."""
        from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent

        return StreamingChatMessageContent(role=AuthorRole.TOOL, choice_index=0, items=[self])

    def to_dict(self) -> dict[str, str]:
        """Convert the instance to a dictionary."""
        return {
            "tool_call_id": self.id,
            "content": self.result,
        }

    @deprecated("The function_name and plugin_name attributes should be used instead.")
    def split_name(self) -> list[str]:
        """Split the name into a plugin and function name."""
        return [self.plugin_name or "", self.function_name]

    def custom_fully_qualified_name(self, separator: str) -> str:
        """Get the fully qualified name of the function with a custom separator.

        Args:
            separator (str): The custom separator.

        Returns:
            The fully qualified name of the function with a custom separator.
        """
        return f"{self.plugin_name}{separator}{self.function_name}" if self.plugin_name else self.function_name

    @field_serializer("result")
    def serialize_result(self, value: Any) -> str:
        """Serialize the result."""
        return str(value)

    def __hash__(self) -> int:
        """Return the hash of the function result content."""
        hashable_result = make_hashable(self.result)
        return hash((
            self.tag,
            self.id,
            hashable_result,
            self.name,
            self.function_name,
            self.plugin_name,
            self.encoding,
        ))
