# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

from enum import Enum
from typing import Any, Union, overload
from xml.etree.ElementTree import Element

from defusedxml import ElementTree
from pydantic import Field

from semantic_kernel.contents.author_role import AuthorRole
from semantic_kernel.contents.const import (
    CHAT_MESSAGE_CONTENT_TAG,
    FUNCTION_CALL_CONTENT_TAG,
    FUNCTION_RESULT_CONTENT_TAG,
    TEXT_CONTENT_TAG,
)
from semantic_kernel.contents.finish_reason import FinishReason
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.kernel_content import KernelContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.kernel_pydantic import KernelBaseModel

TAG_CONTENT_MAP = {
    TEXT_CONTENT_TAG: TextContent,
    FUNCTION_CALL_CONTENT_TAG: FunctionCallContent,
    FUNCTION_RESULT_CONTENT_TAG: FunctionResultContent,
}

ITEM_TYPES = Union[TextContent, FunctionCallContent, FunctionResultContent]


class ChatMessageContent(KernelContent):
    """This is the base class for chat message response content.

    All Chat Completion Services should return a instance of this class as response.
    Or they can implement their own subclass of this class and return an instance.

    Args:
        inner_content: Optional[Any] - The inner content of the response,
            this should hold all the information from the response so even
            when not creating a subclass a developer can leverage the full thing.
        ai_model_id: Optional[str] - The id of the AI model that generated this response.
        metadata: Dict[str, Any] - Any metadata that should be attached to the response.
        role: ChatRole - The role of the chat message.
        content: Optional[str] - The text of the response.
        encoding: Optional[str] - The encoding of the text.

    Methods:
        __str__: Returns the content of the response.
    """

    role: AuthorRole
    name: str | None = None
    items: list[ITEM_TYPES] = Field(default_factory=list)
    encoding: str | None = None
    finish_reason: FinishReason | None = None

    @overload
    def __init__(
        self,
        role: AuthorRole,
        items: list[ITEM_TYPES],
        name: str | None = None,
        inner_content: Any | None = None,
        encoding: str | None = None,
        finish_reason: FinishReason | None = None,
        ai_model_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
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
        name: str | None = None,
        inner_content: Any | None = None,
        encoding: str | None = None,
        finish_reason: FinishReason | None = None,
        ai_model_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
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
        items: list[ITEM_TYPES] | None = None,
        content: str | None = None,
        inner_content: Any | None = None,
        name: str | None = None,
        encoding: str | None = None,
        finish_reason: FinishReason | None = None,
        ai_model_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ):
        kwargs["role"] = role
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

    @property
    def content(self) -> str:
        """Get the content of the response."""
        for item in self.items:
            if isinstance(item, TextContent):
                return item.text
        return ""

    @content.setter
    def content(self, value: str):
        """Set the content of the response."""
        if not value:
            return
        for item in self.items:
            if isinstance(item, TextContent):
                item.text = value
                item.encoding = self.encoding
                return
        self.items.append(
            TextContent(
                ai_model_id=self.ai_model_id,
                inner_content=self.inner_content,
                metadata=self.metadata,
                text=value,
                encoding=self.encoding,
            )
        )

    def __str__(self) -> str:
        return self.content or ""

    def to_element(self) -> "Element":
        """Convert the ChatMessageContent to an XML Element.

        Args:
            root_key: str - The key to use for the root of the XML Element.

        Returns:
            Element - The XML Element representing the ChatMessageContent.
        """
        root = Element(CHAT_MESSAGE_CONTENT_TAG)
        for field in self.model_fields_set:
            if field in ["items", "metadata", "inner_content"]:
                continue
            value = getattr(self, field)
            if value is None:
                continue
            if isinstance(value, Enum):
                value = value.value
            if isinstance(value, KernelBaseModel):
                value = value.model_dump_json(exclude_none=True)
            if isinstance(value, list):
                if isinstance(value[0], KernelBaseModel):
                    value = "|".join([val.model_dump_json(exclude_none=True) for val in value])
                else:
                    value = "|".join(value)
            root.set(field, value)
        for index, item in enumerate(self.items):
            root.insert(index, item.to_element())
        return root

    @classmethod
    def from_element(cls, element: Element) -> "ChatMessageContent":
        """Create a new instance of ChatMessageContent from a XML element.

        Args:
            element: Element - The XML Element to create the ChatMessageContent from.

        Returns:
            ChatMessageContent - The new instance of ChatMessageContent or a subclass.
        """
        items: list[KernelContent] = []
        for child in element:
            items.append(TAG_CONTENT_MAP[child.tag].from_element(child))
        kwargs: dict[str, Any] = {}
        if items:
            kwargs["items"] = items
        if element.text:
            kwargs["content"] = element.text
        if not kwargs:
            raise ValueError("ChatMessageContent must have either items or content.")
        for key, value in element.items():
            kwargs[key] = value
        return cls(**kwargs)

    def to_prompt(self) -> str:
        """Convert the ChatMessageContent to a prompt.

        Returns:
            str - The prompt from the ChatMessageContent.
        """

        root = self.to_element()
        return ElementTree.tostring(root, encoding=self.encoding or "unicode", short_empty_elements=False)

    def to_dict(self, role_key: str = "role", content_key: str = "content") -> dict[str, Any]:
        """Serialize the ChatMessageContent to a dictionary.

        Returns:
            dict - The dictionary representing the ChatMessageContent.
        """
        ret = {
            role_key: self.role.value,
        }
        if self.role == AuthorRole.ASSISTANT and any(isinstance(item, FunctionCallContent) for item in self.items):
            ret["tool_calls"] = [item.to_dict() for item in self.items if isinstance(item, FunctionCallContent)]
        else:
            ret[content_key] = self._parse_items()
        if self.role == AuthorRole.TOOL:
            ret["tool_call_id"] = self.items[0].id or ""
        if self.role == AuthorRole.USER and self.name:
            ret["name"] = self.name
        return ret

    def _parse_items(self) -> str | list[dict[str, Any]]:
        """Parse the items of the ChatMessageContent.

        Returns:
            str | dict - The parsed items.
        """
        if len(self.items) == 1:
            return str(self.items[0])
        return [item.to_dict() for item in self.items]
