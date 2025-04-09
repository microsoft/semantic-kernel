# Copyright (c) Microsoft. All rights reserved.

import logging
from enum import Enum
from html import unescape
from typing import Annotated, Any, ClassVar, Literal, overload
from xml.etree.ElementTree import Element  # nosec

from defusedxml import ElementTree
from pydantic import Field

from semantic_kernel.contents.annotation_content import AnnotationContent
from semantic_kernel.contents.audio_content import AudioContent
from semantic_kernel.contents.binary_content import BinaryContent
from semantic_kernel.contents.const import (
    ANNOTATION_CONTENT_TAG,
    CHAT_MESSAGE_CONTENT_TAG,
    DISCRIMINATOR_FIELD,
    FILE_REFERENCE_CONTENT_TAG,
    FUNCTION_CALL_CONTENT_TAG,
    FUNCTION_RESULT_CONTENT_TAG,
    IMAGE_CONTENT_TAG,
    STREAMING_ANNOTATION_CONTENT_TAG,
    STREAMING_FILE_REFERENCE_CONTENT_TAG,
    TEXT_CONTENT_TAG,
    ContentTypes,
)
from semantic_kernel.contents.file_reference_content import FileReferenceContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.image_content import ImageContent
from semantic_kernel.contents.kernel_content import KernelContent
from semantic_kernel.contents.streaming_annotation_content import StreamingAnnotationContent
from semantic_kernel.contents.streaming_file_reference_content import StreamingFileReferenceContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.contents.utils.finish_reason import FinishReason
from semantic_kernel.contents.utils.hashing import make_hashable
from semantic_kernel.contents.utils.status import Status
from semantic_kernel.exceptions.content_exceptions import ContentInitializationError

TAG_CONTENT_MAP = {
    ANNOTATION_CONTENT_TAG: AnnotationContent,
    TEXT_CONTENT_TAG: TextContent,
    FILE_REFERENCE_CONTENT_TAG: FileReferenceContent,
    FUNCTION_CALL_CONTENT_TAG: FunctionCallContent,
    FUNCTION_RESULT_CONTENT_TAG: FunctionResultContent,
    IMAGE_CONTENT_TAG: ImageContent,
    STREAMING_FILE_REFERENCE_CONTENT_TAG: StreamingFileReferenceContent,
    STREAMING_ANNOTATION_CONTENT_TAG: StreamingAnnotationContent,
}

CMC_ITEM_TYPES = Annotated[
    AnnotationContent
    | BinaryContent
    | ImageContent
    | TextContent
    | FunctionResultContent
    | FunctionCallContent
    | FileReferenceContent
    | StreamingAnnotationContent
    | StreamingFileReferenceContent
    | AudioContent,
    Field(discriminator=DISCRIMINATOR_FIELD),
]


logger = logging.getLogger(__name__)


class ChatMessageContent(KernelContent):
    """This is the class for chat message response content.

    All Chat Completion Services should return an instance of this class as response.
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

    content_type: Literal[ContentTypes.CHAT_MESSAGE_CONTENT] = Field(default=CHAT_MESSAGE_CONTENT_TAG, init=False)  # type: ignore
    tag: ClassVar[str] = CHAT_MESSAGE_CONTENT_TAG
    role: AuthorRole
    name: str | None = None
    items: list[CMC_ITEM_TYPES] = Field(default_factory=list)
    encoding: str | None = None
    finish_reason: FinishReason | None = None
    status: Status | None = None

    @overload
    def __init__(
        self,
        role: AuthorRole,
        items: list[CMC_ITEM_TYPES],
        name: str | None = None,
        inner_content: Any | None = None,
        encoding: str | None = None,
        finish_reason: FinishReason | None = None,
        status: Status | None = None,
        ai_model_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None: ...

    @overload
    def __init__(
        self,
        role: AuthorRole,
        content: str,
        name: str | None = None,
        inner_content: Any | None = None,
        encoding: str | None = None,
        finish_reason: FinishReason | None = None,
        status: Status | None = None,
        ai_model_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None: ...

    def __init__(  # type: ignore
        self,
        role: AuthorRole,
        items: list[CMC_ITEM_TYPES] | None = None,
        content: str | None = None,
        inner_content: Any | None = None,
        name: str | None = None,
        encoding: str | None = None,
        finish_reason: FinishReason | None = None,
        status: Status | None = None,
        ai_model_id: str | None = None,
        metadata: dict[str, Any] | None = None,
        **kwargs: Any,
    ):
        """Create a ChatMessageContent instance.

        Args:
            role: AuthorRole - The role of the chat message.
            items: list[TextContent, StreamingTextContent, FunctionCallContent, FunctionResultContent, ImageContent]
                 - The content.
            content: str - The text of the response.
            inner_content: Optional[Any] - The inner content of the response,
                this should hold all the information from the response so even
                when not creating a subclass a developer can leverage the full thing.
            name: Optional[str] - The name of the response.
            encoding: Optional[str] - The encoding of the text.
            finish_reason: Optional[FinishReason] - The reason the response was finished.
            status: Optional[Status] - The status of the response for the Responses API.
            ai_model_id: Optional[str] - The id of the AI model that generated this response.
            metadata: Dict[str, Any] - Any metadata that should be attached to the response.
            **kwargs: Any - Any additional fields to set on the instance.
        """
        kwargs["role"] = role
        if encoding:
            kwargs["encoding"] = encoding
        if finish_reason:
            kwargs["finish_reason"] = finish_reason
        if status:
            kwargs["status"] = status
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
        """Get the content of the response, will find the first TextContent's text."""
        for item in self.items:
            if isinstance(item, TextContent):
                return item.text
        return ""

    @content.setter
    def content(self, value: str):
        """Set the content of the response."""
        if not value:
            logger.warning(
                "Setting empty content on ChatMessageContent does not work, "
                "you can do this through the underlying items if needed, ignoring."
            )
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
        """Get the content of the response as a string."""
        return self.content or ""

    def to_element(self) -> "Element":
        """Convert the ChatMessageContent to an XML Element.

        Args:
            root_key: str - The key to use for the root of the XML Element.

        Returns:
            Element - The XML Element representing the ChatMessageContent.
        """
        root = Element(self.tag)
        for field in self.model_fields_set:
            if field not in ["role", "name", "encoding", "finish_reason", "ai_model_id"]:
                continue
            value = getattr(self, field)
            if isinstance(value, Enum):
                value = value.value
            root.set(field, value)
        for index, item in enumerate(self.items):
            root.insert(index, item.to_element())
        return root

    @classmethod
    def from_element(cls, element: Element) -> "ChatMessageContent":
        """Create a new instance of ChatMessageContent from an XML element.

        Args:
            element: Element - The XML Element to create the ChatMessageContent from.

        Returns:
            ChatMessageContent - The new instance of ChatMessageContent or a subclass.
        """
        if element.tag != cls.tag:
            raise ContentInitializationError(f"Element tag is not {cls.tag}")  # pragma: no cover
        kwargs: dict[str, Any] = {key: value for key, value in element.items()}
        items: list[KernelContent] = []
        if element.text:
            items.append(TextContent(text=unescape(element.text)))
        for child in element:
            if child.tag not in TAG_CONTENT_MAP:
                logger.warning('Unknown tag "%s" in ChatMessageContent, treating as text', child.tag)
                text = ElementTree.tostring(child, encoding="unicode", short_empty_elements=False)
                items.append(TextContent(text=unescape(text) or ""))
            else:
                items.append(TAG_CONTENT_MAP[child.tag].from_element(child))  # type: ignore
        if len(items) == 1 and isinstance(items[0], TextContent):
            kwargs["content"] = items[0].text
        elif all(isinstance(item, TextContent) for item in items):
            kwargs["content"] = "".join(item.text for item in items)  # type: ignore
        else:
            kwargs["items"] = items
        if "choice_index" in kwargs and cls is ChatMessageContent:
            logger.info(
                "Seems like you are trying to create a StreamingChatMessageContent, "
                "use StreamingChatMessageContent.from_element instead, ignoring that field "
                "and creating a ChatMessageContent instance."
            )
            kwargs.pop("choice_index")
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
        ret: dict[str, Any] = {
            role_key: self.role.value,
        }
        if self.role == AuthorRole.ASSISTANT and any(isinstance(item, FunctionCallContent) for item in self.items):
            ret["tool_calls"] = [item.to_dict() for item in self.items if isinstance(item, FunctionCallContent)]
        else:
            ret[content_key] = self._parse_items()
        if self.role == AuthorRole.TOOL:
            assert isinstance(self.items[0], FunctionResultContent)  # nosec
            ret["tool_call_id"] = self.items[0].id or ""
        if self.role != AuthorRole.TOOL and self.name:
            ret["name"] = self.name
        return ret

    def _parse_items(self) -> str | list[dict[str, Any]]:
        """Parse the items of the ChatMessageContent.

        Returns:
            str | list of dicts - The parsed items.
        """
        if len(self.items) == 1 and isinstance(self.items[0], TextContent):
            return self.items[0].text
        if len(self.items) == 1 and isinstance(self.items[0], FunctionResultContent):
            return str(self.items[0].result)
        return [item.to_dict() for item in self.items]

    def __hash__(self) -> int:
        """Return the hash of the chat message content."""
        hashable_items = [make_hashable(item) for item in self.items] if self.items else []
        return hash((self.tag, self.role, self.content, self.encoding, self.finish_reason, *hashable_items))
