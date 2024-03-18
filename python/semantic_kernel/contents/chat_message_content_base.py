# Copyright (c) Microsoft. All rights reserved.
import sys
from typing import TYPE_CHECKING, Any, Dict, Union

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated

from xml.etree.ElementTree import Element

from pydantic import Field, RootModel

if TYPE_CHECKING:
    from semantic_kernel.connectors.ai.open_ai.contents.azure_chat_message_content import AzureChatMessageContent
    from semantic_kernel.connectors.ai.open_ai.contents.open_ai_chat_message_content import OpenAIChatMessageContent
    from semantic_kernel.contents.chat_message_content import ChatMessageContent


class ChatMessageContentBase(RootModel):
    """Base class for all chat message content types.

    This class is used to dynamically create a certain type of ChatMessageContent, baed on the type field.
    Please use this class always through the classmethods, from_dict, from_fields or from_element.
    If you don't do that, you need to manually rebuild the model with the model_rebuild method,
    after importing the ChatMessageContent and all it's subclasses. And you then have to use the root field.

    The first two use dictionaries, directly or as kwargs to create the ChatMessageContent,
    the last one uses an XML Element to create the ChatMessageContent.
    All these methods then return the root field of the ChatMessageContentBase,
      which is a instance of ChatMessageContent or the requested subclass.
    """

    root: Annotated[
        Union["ChatMessageContent", "OpenAIChatMessageContent", "AzureChatMessageContent"],
        Field(discriminator="type"),
    ]

    @classmethod
    def from_fields(cls, **kwargs: Any) -> "ChatMessageContent":
        """Create a new instance of ChatMessageContent from fields.

        Args:
            kwargs: Any - The keyword arguments to create the ChatMessageContent with.

        Returns:
            ChatMessageContent - The new instance of ChatMessageContent or a subclass.
        """
        from semantic_kernel.connectors.ai.open_ai.contents.azure_chat_message_content import AzureChatMessageContent  # noqa: F401
        from semantic_kernel.connectors.ai.open_ai.contents.open_ai_chat_message_content import OpenAIChatMessageContent  # noqa: F401
        from semantic_kernel.contents.chat_message_content import ChatMessageContent  # noqa: F401

        cls.model_rebuild()
        if "type" not in kwargs:
            kwargs["type"] = "ChatMessageContent"
        return cls(**kwargs).root

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ChatMessageContent":
        """Create a new instance of ChatMessageContent from a dictionary.

        Args:
            data: Dict[str, Any] - The dictionary to create the ChatMessageContent from.

        Returns:
            ChatMessageContent - The new instance of ChatMessageContent or a subclass.
        """
        return cls.from_fields(**data)

    @classmethod
    def from_element(cls, element: Element) -> "ChatMessageContent":
        """Create a new instance of ChatMessageContent from a XML element.

        Args:
            element: Element - The XML Element to create the ChatMessageContent from.

        Returns:
            ChatMessageContent - The new instance of ChatMessageContent or a subclass.
        """
        kwargs: Dict[str, Any] = {"content": element.text}
        for key, value in element.items():
            kwargs[key] = value
        return cls.from_fields(**kwargs)
