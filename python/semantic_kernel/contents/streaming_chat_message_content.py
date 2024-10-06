# Copyright (c) Microsoft. All rights reserved.

from enum import Enum
from typing import Any, Union, overload
from xml.etree.ElementTree import Element  # nosec

from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.image_content import ImageContent
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
from semantic_kernel.contents.streaming_content_mixin import StreamingContentMixin
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
from semantic_kernel.contents.streaming_content_mixin import StreamingContentMixin
=======
from semantic_kernel.contents.streaming_annotation_content import StreamingAnnotationContent
from semantic_kernel.contents.streaming_content_mixin import StreamingContentMixin
from semantic_kernel.contents.streaming_file_reference_content import StreamingFileReferenceContent
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
from semantic_kernel.contents.streaming_annotation_content import StreamingAnnotationContent
from semantic_kernel.contents.streaming_content_mixin import StreamingContentMixin
from semantic_kernel.contents.streaming_file_reference_content import StreamingFileReferenceContent
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.contents.utils.finish_reason import FinishReason
from semantic_kernel.exceptions import ContentAdditionException

ITEM_TYPES = Union[
    ImageContent,
    StreamingTextContent,
    FunctionCallContent,
    FunctionResultContent,
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
    StreamingFileReferenceContent,
    StreamingAnnotationContent,
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
    StreamingFileReferenceContent,
    StreamingAnnotationContent,
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
]


class StreamingChatMessageContent(ChatMessageContent, StreamingContentMixin):
    """This is the class for streaming chat message response content.

    All Chat Completion Services should return an instance of this class as streaming response,
    where each part of the response as it is streamed is converted to an instance of this class,
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
from typing import Optional

from semantic_kernel.contents.chat_role import ChatRole
from semantic_kernel.contents.finish_reason import FinishReason
from semantic_kernel.contents.streaming_kernel_content import StreamingKernelContent


class StreamingChatMessageContent(StreamingKernelContent):
    """This is the base class for streaming chat message response content.

    All Chat Completion Services should return a instance of this class as streaming response,
    where each part of the response as it is streamed is converted to a instance of this class,
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
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
        return (
            self.content.encode(self.encoding if self.encoding else "utf-8")
            if self.content
            else b""
        )

    def __add__(
        self, other: "StreamingChatMessageContent"
    ) -> "StreamingChatMessageContent":
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        """When combining two StreamingChatMessageContent instances, the content fields are combined.

        The inner_content of the first one is used, ai_model_id and encoding should be the same,
        if role is set, they should be the same.
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
    role: Optional[ChatRole] = ChatRole.ASSISTANT
    content: Optional[str] = None
    encoding: Optional[str] = None
    finish_reason: Optional[FinishReason] = None

    def __str__(self) -> str:
        return self.content or ""

    def __bytes__(self) -> bytes:
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
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
        """
        if not isinstance(other, StreamingChatMessageContent):
            raise ContentAdditionException(
                f"Cannot add other type to StreamingChatMessageContent, type supplied: {type(other)}"
            )
        if self.choice_index != other.choice_index:
            raise ContentAdditionException(
                "Cannot add StreamingChatMessageContent with different choice_index"
            )
        if self.ai_model_id != other.ai_model_id:
            raise ContentAdditionException(
                "Cannot add StreamingChatMessageContent from different ai_model_id"
            )
        if self.encoding != other.encoding:
            raise ContentAdditionException(
                "Cannot add StreamingChatMessageContent with different encoding"
            )
        if self.role and other.role and self.role != other.role:
            raise ContentAdditionException(
                "Cannot add StreamingChatMessageContent with different role"
            )
        if self.items or other.items:
            for other_item in other.items:
                added = False
                for id, item in enumerate(list(self.items)):
                    if type(item) is type(other_item) and hasattr(item, "__add__"):
                        try:
                            new_item = item + other_item  # type: ignore
                            self.items[id] = new_item
                            added = True
                        except (ValueError, ContentAdditionException):
                            continue
                if not added:
                    self.items.append(other_item)
        if not isinstance(self.inner_content, list):
            self.inner_content = [self.inner_content] if self.inner_content else []
        other_content = (
            other.inner_content
            if isinstance(other.inner_content, list)
            else [other.inner_content] if other.inner_content else []
        )
        self.inner_content.extend(other_content)
        return StreamingChatMessageContent(
            role=self.role,
            items=self.items,  # type: ignore
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
            choice_index=self.choice_index,
            inner_content=self.inner_content,
            ai_model_id=self.ai_model_id,
            metadata=self.metadata,
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
        if self.choice_index != other.choice_index:
            raise ValueError("Cannot add StreamingChatMessageContent with different choice_index")
        if self.ai_model_id != other.ai_model_id:
            raise ValueError("Cannot add StreamingChatMessageContent from different ai_model_id")
        if self.encoding != other.encoding:
            raise ValueError("Cannot add StreamingChatMessageContent with different encoding")
        if self.role and other.role and self.role != other.role:
            raise ValueError("Cannot add StreamingChatMessageContent with different role")
        return StreamingChatMessageContent(
            raise ContentAdditionException("Cannot add StreamingChatMessageContent with different role")

        return StreamingChatMessageContent(
            role=self.role,
            items=self._merge_items_lists(other.items),
            choice_index=self.choice_index,
            inner_content=self._merge_inner_contents(other.inner_content),
            ai_model_id=self.ai_model_id,
            metadata=self.metadata,
            metadata=self.metadata | other.metadata,
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
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
            if field not in [
                "role",
                "name",
                "encoding",
                "finish_reason",
                "ai_model_id",
                "choice_index",
            ]:
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
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
            role=self.role,
            content=(self.content or "") + (other.content or ""),
            encoding=self.encoding,
            finish_reason=self.finish_reason or other.finish_reason,
        )
        

    def __hash__(self) -> int:
        """Return the hash of the streaming chat message content."""
        return hash((
            self.tag,
            self.role,
            self.content,
            self.encoding,
            self.finish_reason,
            self.choice_index,
            *self.items,
        ))
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
