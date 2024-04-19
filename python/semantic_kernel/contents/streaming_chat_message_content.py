# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

from typing import Any, overload

from semantic_kernel.contents.author_role import AuthorRole
from semantic_kernel.contents.chat_message_content import ITEM_TYPES, ChatMessageContent
from semantic_kernel.contents.finish_reason import FinishReason
from semantic_kernel.contents.streaming_content_mixin import StreamingContentMixin
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.exceptions import ContentAdditionException


class StreamingChatMessageContent(ChatMessageContent, StreamingContentMixin):
    """This is the base class for streaming chat message response content.

    All Chat Completion Services should return a instance of this class as streaming response,
    where each part of the response as it is streamed is converted to a instance of this class,
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
    ) -> None:
        """All Chat Completion Services should return a instance of this class as response.
        Or they can implement their own subclass of this class and return an instance.

        Args:
            inner_content: Optional[Any] - The inner content of the response,
                this should hold all the information from the response so even
                when not creating a subclass a developer can leverage the full thing.
            ai_model_id: Optional[str] - The id of the AI model that generated this response.
            metadata: Dict[str, Any] - Any metadata that should be attached to the response.
            role: ChatRole - The role of the chat message.
            items: list[KernelContent] - The inner content.
            encoding: Optional[str] - The encoding of the text.
        """

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
    ) -> None:
        """All Chat Completion Services should return a instance of this class as response.
        Or they can implement their own subclass of this class and return an instance.

        Args:
            inner_content: Optional[Any] - The inner content of the response,
                this should hold all the information from the response so even
                when not creating a subclass a developer can leverage the full thing.
            ai_model_id: Optional[str] - The id of the AI model that generated this response.
            metadata: Dict[str, Any] - Any metadata that should be attached to the response.
            role: ChatRole - The role of the chat message.
            content: str - The text of the response.
            encoding: Optional[str] - The encoding of the text.
        """

    def __init__(
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
            item = TextContent(
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
        if not items:
            raise ValueError("ChatMessageContent must have either items or content.")
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
        return self.content.encode(self.encoding if self.encoding else "utf-8") if self.content else b""

    def __add__(self, other: StreamingChatMessageContent) -> StreamingChatMessageContent:
        """When combining two StreamingChatMessageContent instances, the content fields are combined.

        The inner_content of the first one is used, ai_model_id and encoding should be the same,
        if role is set, they should be the same.
        """
        if self.choice_index != other.choice_index:
            raise ContentAdditionException("Cannot add StreamingChatMessageContent with different choice_index")
        if self.ai_model_id != other.ai_model_id:
            raise ContentAdditionException("Cannot add StreamingChatMessageContent from different ai_model_id")
        if self.encoding != other.encoding:
            raise ContentAdditionException("Cannot add StreamingChatMessageContent with different encoding")
        if self.role and other.role and self.role != other.role:
            raise ContentAdditionException("Cannot add StreamingChatMessageContent with different role")
        for id, item in enumerate(self.items):
            item += other.items[id]
        return StreamingChatMessageContent(
            choice_index=self.choice_index,
            inner_content=self.inner_content,
            ai_model_id=self.ai_model_id,
            metadata=self.metadata,
            role=self.role,
            items=self.items,
            encoding=self.encoding,
            finish_reason=self.finish_reason or other.finish_reason,
        )
