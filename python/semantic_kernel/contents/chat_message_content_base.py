# Copyright (c) Microsoft. All rights reserved.
import sys
from typing import TYPE_CHECKING, Union

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
    root: Annotated[
        Union["ChatMessageContent", "OpenAIChatMessageContent", "AzureChatMessageContent"], Field(discriminator="type")
    ]

    @classmethod
    def from_element(cls, element: Element) -> "ChatMessageContentBase":
        """Create a new instance of ChatMessageContent from a prompt.

        Args:
            prompt: str - The prompt to create the ChatMessageContent from.

        Returns:
            ChatMessageContent - The new instance of ChatMessageContent.
        """
        from semantic_kernel.connectors.ai.open_ai.contents.azure_chat_message_content import AzureChatMessageContent  # noqa: F401
        from semantic_kernel.connectors.ai.open_ai.contents.open_ai_chat_message_content import OpenAIChatMessageContent  # noqa: F401
        from semantic_kernel.contents.chat_message_content import ChatMessageContent  # noqa: F401

        cls.model_rebuild()
        args = {"content": element.text}
        for key, value in element.items():
            args[key] = value
        if not args.get("type"):
            args["type"] = "ChatMessageContent"
        return cls(**args)
