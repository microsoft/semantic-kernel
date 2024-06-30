# Copyright (c) Microsoft. All rights reserved.

from enum import Enum
from typing import Any, Union, overload
from xml.etree.ElementTree import Element  # nosec

from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.image_content import ImageContent
from semantic_kernel.contents.streaming_content_mixin import StreamingContentMixin
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.contents.utils.finish_reason import FinishReason
from semantic_kernel.exceptions import ContentAdditionException

ITEM_TYPES = Union[
    ImageContent,
    StreamingTextContent,
    FunctionCallContent,
    FunctionResultContent,
]


class StreamingChatMessageContent(ChatMessageContent, StreamingContentMixin):
    """This is the class for streaming chat message response content.

    All Chat Completion Services should return an instance of this class as streaming response,
    where each part of the response as it is streamed is converted to an instance of this class,
    the end-user will have to either do something directly or gather them and combine them into a
    new instance. A service can implement their own subclass of this class and return instances of that.

    Args:
        choice_index: int - The index of the choice that generated this response.
        inner_content: Optional[Any] - The inner content of the response,
            this should hold all the information from the response so even
            when not creating a subclass a developer can leverage the full thing.
        ai_model_id: Optional[str] - The id of the AI model that generated this response.
        metadata: Dict[str, Any] - Any metadata that should be attached to the response.
        role: Optional[ChatRole] - The role of the chat message, defaults to ASSISTANT.
        content: Optional[str] - The text of the response.
        encoding: Optional[str] - The encoding of the text.

    Methods:
        __str__: Returns the content of the response.
        __bytes__: Returns the content of the response encoded in the encoding.
        __add__: Combines two StreamingChatMessageContent instances.
    """

    @overload
    def __init__(
        self,
        role: AuthorRole,
        items: list[ITEM_TYPES],
        choice_index: int,
        name: str | None = None,
        inner_content: Any | None = None,
        encoding: str | None = None,
        finish_reason: FinishReason | None = None,
        ai_model_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None: ...

    @overload
    def __init__(
        self,
        role: AuthorRole,
        content: str,
        choice_index: int,
        name: str | None = None,
        inner_content: Any | None = None,
        encoding: str | None = None,
        finish_reason: FinishReason | None = None,
        ai_model_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None: ...

    def __init__(  # type: ignore
        self,
        role: AuthorRole,
        choice_index: int,
        items: list[ITEM_TYPES] | None = None,
        content: str | None = None,
        inner_content: Any | None = None,
        name: str | None = None,
        encoding: str | None = None,
        finish_reason: FinishReason | None = None,
        ai_model_id: str | None = None,
        metadata: dict[str, Any] | None = None,
    ):
        """Create a new instance of StreamingChatMessageContent.

        Args:
            role: ChatRole - The role of the chat message.
            choice_index: int - The index of the choice that generated this response.
            items: list[TextContent, FunctionCallContent, FunctionResultContent, ImageContent] - The content.
            content: str - The text of the response.
            inner_content: Optional[Any] - The inner content of the response,
                this should hold all the information from the response so even
                when not creating a subclass a developer can leverage the full thing.
            name: Optional[str] - The name of the response.
            encoding: Optional[str] - The encoding of the text.
            finish_reason: Optional[FinishReason] - The reason the response was finished.
            metadata: Dict[str, Any] - Any metadata that should be attached to the response.
            ai_model_id: Optional[str] - The id of the AI model that generated this response.
        """
        kwargs: dict[str, Any] = {
            "role": role,
            "choice_index": choice_index,
        }
        if encoding:
            kwargs["encoding"] = encoding
        if finish_reason:
            kwargs["finish_reason"] = finish_reason
        if name:
            kwargs["name"] = name
        if content:
            item = StreamingTextContent(
                choice_index=choice_index,
                ai_model_id=ai_model_id,
                inner_content=inner_content,
                metadata=metadata or {},
                text=content,
                encoding=encoding,
            )
            if items:
                items.append(item)
            else:
                items = [item]
        if items:
            kwargs["items"] = items
        if inner_content:
            kwargs["inner_content"] = inner_content
        if metadata:
            kwargs["metadata"] = metadata
        if ai_model_id:
            kwargs["ai_model_id"] = ai_model_id
        super().__init__(
            **kwargs,
        )

    def __bytes__(self) -> bytes:
        """Return the content of the response encoded in the encoding."""
        return self.content.encode(self.encoding if self.encoding else "utf-8") if self.content else b""

    def __add__(self, other: "StreamingChatMessageContent") -> "StreamingChatMessageContent":
        """When combining two StreamingChatMessageContent instances, the content fields are combined.

        The inner_content of the first one is used, ai_model_id and encoding should be the same,
        if role is set, they should be the same.
        """
        if not isinstance(other, StreamingChatMessageContent):
            raise ContentAdditionException(
                f"Cannot add other type to StreamingChatMessageContent, type supplied: {type(other)}"
            )
        if self.choice_index != other.choice_index:
            raise ContentAdditionException("Cannot add StreamingChatMessageContent with different choice_index")
        if self.ai_model_id != other.ai_model_id:
            raise ContentAdditionException("Cannot add StreamingChatMessageContent from different ai_model_id")
        if self.encoding != other.encoding:
            raise ContentAdditionException("Cannot add StreamingChatMessageContent with different encoding")
        if self.role and other.role and self.role != other.role:
            raise ContentAdditionException("Cannot add StreamingChatMessageContent with different role")
        if self.items or other.items:
            for other_item in other.items:
                added = False
                for id, item in enumerate(list(self.items)):
                    if type(item) is type(other_item) and hasattr(item, "__add__"):
                        try:
                            new_item = item + other_item  # type: ignore
                            self.items[id] = new_item
                            added = True
                        except ValueError:
                            continue
                if not added:
                    self.items.append(other_item)
        if not isinstance(self.inner_content, list):
            self.inner_content = [self.inner_content] if self.inner_content else []
        other_content = (
            other.inner_content
            if isinstance(other.inner_content, list)
            else [other.inner_content]
            if other.inner_content
            else []
        )
        self.inner_content.extend(other_content)
        return StreamingChatMessageContent(
            role=self.role,
            items=self.items,  # type: ignore
            choice_index=self.choice_index,
            inner_content=self.inner_content,
            ai_model_id=self.ai_model_id,
            metadata=self.metadata,
            encoding=self.encoding,
            finish_reason=self.finish_reason or other.finish_reason,
        )

    def to_element(self) -> "Element":
        """Convert the StreamingChatMessageContent to an XML Element.

        Args:
            root_key: str - The key to use for the root of the XML Element.

        Returns:
            Element - The XML Element representing the StreamingChatMessageContent.
        """
        root = Element(self.tag)
        for field in self.model_fields_set:
            if field not in ["role", "name", "encoding", "finish_reason", "ai_model_id", "choice_index"]:
                continue
            value = getattr(self, field)
            if isinstance(value, Enum):
                value = value.value
            if isinstance(value, int):
                value = str(value)
            root.set(field, value)
        for index, item in enumerate(self.items):
            root.insert(index, item.to_element())
        return root
