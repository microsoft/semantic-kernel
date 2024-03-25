# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

import json
from xml.etree.ElementTree import Element

from defusedxml import ElementTree

from semantic_kernel.contents.chat_role import ChatRole
from semantic_kernel.contents.kernel_content import KernelContent


class ChatMessageContent(KernelContent):
    """This is the base class for chat message response content.

    All Chat Completion Services should return a instance of this class as response.
    Or they can implement their own subclass of this class and return an instance.

    Args:
        inner_content: Any | None - The inner content of the response,
            this should hold all the information from the response so even
            when not creating a subclass a developer can leverage the full thing.
        ai_model_id: str | None - The id of the AI model that generated this response.
        metadata: dict[str, Any] - Any metadata that should be attached to the response.
        role: ChatRole - The role of the chat message.
        content: str | None - The text of the response.
        encoding: str | None - The encoding of the text.

    Methods:
        __str__: Returns the content of the response.
    """

    role: ChatRole
    content: str | None = None
    encoding: str | None = None

    def __str__(self) -> str:
        return self.content or ""

    def to_element(self, root_key: str) -> Element:
        """Convert the ChatMessageContent to an XML Element.

        Args:
            root_key: str - The key to use for the root of the XML Element.

        Returns:
            Element - The XML Element representing the ChatMessageContent.
        """
        root = Element(root_key)
        root.set("role", self.role.value)
        root.text = self.content or ""
        return root

    def to_prompt(self, root_key: str) -> str:
        """Convert the ChatMessageContent to a prompt.

        Returns:
            str - The prompt from the ChatMessageContent.
        """

        root = self.to_element(root_key)
        return ElementTree.tostring(root, encoding=self.encoding or "unicode", short_empty_elements=False)

    @classmethod
    def from_element(cls, element: Element) -> "ChatMessageContent":
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
