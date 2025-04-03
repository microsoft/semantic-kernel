# Copyright (c) Microsoft. All rights reserved.

from enum import Enum
from typing import Annotated, Any, overload
from xml.etree.ElementTree import Element  # nosec

from pydantic import Field

from semantic_kernel.contents.audio_content import AudioContent
from semantic_kernel.contents.binary_content import BinaryContent
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.const import DISCRIMINATOR_FIELD
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.image_content import ImageContent
from semantic_kernel.contents.streaming_annotation_content import StreamingAnnotationContent
from semantic_kernel.contents.streaming_content_mixin import StreamingContentMixin
from semantic_kernel.contents.streaming_file_reference_content import StreamingFileReferenceContent
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.contents.utils.finish_reason import FinishReason
from semantic_kernel.contents.utils.hashing import make_hashable
from semantic_kernel.exceptions import ContentAdditionException

STREAMING_CMC_ITEM_TYPES = Annotated[
    BinaryContent
    | AudioContent
    | ImageContent
    | FunctionResultContent
    | FunctionCallContent
    | StreamingTextContent
    | StreamingAnnotationContent
    | StreamingFileReferenceContent,
    Field(discriminator=DISCRIMINATOR_FIELD),
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

    function_invoke_attempt: int | None = Field(
        default=0,
        description="Tracks the current attempt count for automatically invoking functions. "
        "This value increments with each subsequent automatic invocation attempt.",
    )

    @overload
    def __init__(
        self,
        role: AuthorRole,
        items: list[STREAMING_CMC_ITEM_TYPES],
        choice_index: int,
        name: str | None = None,
        inner_content: Any | None = None,
        encoding: str | None = None,
        finish_reason: FinishReason | None = None,
        ai_model_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        function_invoke_attempt: int | None = None,
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
        function_invoke_attempt: int | None = None,
    ) -> None: ...

    def __init__(  # type: ignore
        self,
        role: AuthorRole,
        choice_index: int,
        items: list[STREAMING_CMC_ITEM_TYPES] | None = None,
        content: str | None = None,
        inner_content: Any | None = None,
        name: str | None = None,
        encoding: str | None = None,
        finish_reason: FinishReason | None = None,
        ai_model_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        function_invoke_attempt: int | None = None,
    ):
        """Create a new instance of StreamingChatMessageContent.

        Args:
            role: The role of the chat message.
            choice_index: The index of the choice that generated this response.
            items: The content.
            content: The text of the response.
            inner_content: The inner content of the response,
                this should hold all the information from the response so even
                when not creating a subclass a developer can leverage the full thing.
            name: The name of the response.
            encoding: The encoding of the text.
            finish_reason: The reason the response was finished.
            metadata: Any metadata that should be attached to the response.
            ai_model_id: The id of the AI model that generated this response.
            function_invoke_attempt: Tracks the current attempt count for automatically
                invoking functions. This value increments with each subsequent automatic invocation attempt.
        """
        kwargs: dict[str, Any] = {
            "role": role,
            "choice_index": choice_index,
            "function_invoke_attempt": function_invoke_attempt,
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

        The addition should follow these rules:
            1. The inner_content of the two will be combined. If they are not lists, they will be converted to lists.
            2. ai_model_id should be the same.
            3. encoding should be the same.
            4. role should be the same.
            5. choice_index should be the same.
            6. Metadata will be combined
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

        return StreamingChatMessageContent(
            role=self.role,
            items=self._merge_items_lists(other.items),
            choice_index=self.choice_index,
            inner_content=self._merge_inner_contents(other.inner_content),
            ai_model_id=self.ai_model_id,
            metadata=self.metadata | other.metadata,
            encoding=self.encoding,
            finish_reason=self.finish_reason or other.finish_reason,
            function_invoke_attempt=self.function_invoke_attempt,
            name=self.name or other.name,
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

    def __hash__(self) -> int:
        """Return the hash of the streaming chat message content."""
        hashable_items = [make_hashable(item) for item in self.items] if self.items else []
        return hash((
            self.tag,
            self.role,
            self.content,
            self.encoding,
            self.finish_reason,
            self.choice_index,
            self.function_invoke_attempt,
            *hashable_items,
        ))
