# Copyright (c) Microsoft. All rights reserved.

import json
from typing import Optional
from xml.etree.ElementTree import Element

from defusedxml import ElementTree

from semantic_kernel.contents.chat_role import ChatRole
from semantic_kernel.contents.finish_reason import FinishReason
from semantic_kernel.contents.streaming_kernel_content import StreamingKernelContent
from semantic_kernel.exceptions import ContentAdditionException


class StreamingChatMessageContent(StreamingKernelContent):
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
        return StreamingChatMessageContent(
            choice_index=self.choice_index,
            inner_content=self.inner_content,
            ai_model_id=self.ai_model_id,
            metadata=self.metadata,
            role=self.role,
            content=(self.content or "") + (other.content or ""),
            encoding=self.encoding,
            finish_reason=self.finish_reason or other.finish_reason,
        )

    def to_prompt(self, root_key: str) -> str:
        """Convert the ChatMessageContent to a prompt.

        Returns:
            str - The prompt from the ChatMessageContent.
        """

        root = Element(root_key)
        root.set("role", self.role.value)
        root.set("metadata", json.dumps(self.metadata))
        root.text = self.content or ""
        return ElementTree.tostring(root, encoding=self.encoding or "unicode", short_empty_elements=False)

    @classmethod
    def from_element(cls, element: Element) -> "StreamingChatMessageContent":
        """Create a new instance of ChatMessageContent from a prompt.

        Args:
            prompt: str - The prompt to create the ChatMessageContent from.

        Returns:
            ChatMessageContent - The new instance of ChatMessageContent.
        """
        args = {"role": element.get("role", ChatRole.USER.value), "content": element.text}
        if metadata := element.get("metadata"):
            args["metadata"] = json.loads(metadata)
        return cls(**args)
