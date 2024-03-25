# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

import logging
from typing import Any, Iterator, List
from xml.etree.ElementTree import Element, tostring

from defusedxml.ElementTree import XML, ParseError

from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.chat_message_content_base import ChatMessageContentBase
from semantic_kernel.contents.chat_role import ChatRole
from semantic_kernel.contents.const import (
    CHAT_MESSAGE_CONTENT,
    ROOT_KEY_HISTORY,
    ROOT_KEY_MESSAGE,
    TYPES_CHAT_MESSAGE_CONTENT,
)
from semantic_kernel.exceptions import ContentInitializationError, ContentSerializationError
from semantic_kernel.kernel_pydantic import KernelBaseModel

logger = logging.getLogger(__name__)


class ChatHistory(KernelBaseModel):
    """
    This class holds the history of chat messages from a chat conversation.

    Note: the constructor takes a system_message parameter, which is not part
    of the class definition. This is to allow the system_message to be passed in
    as a keyword argument, but not be part of the class definition.

    Attributes:
        messages (list[ChatMessageContent]): The list of chat messages in the history.
    """

    messages: list["ChatMessageContent"]
    message_type: TYPES_CHAT_MESSAGE_CONTENT = CHAT_MESSAGE_CONTENT

    def __init__(self, **data: Any):
        """
        Initializes a new instance of the ChatHistory class, optionally incorporating a message and/or
        a system message at the beginning of the chat history.

        This constructor allows for flexible initialization with chat messages and an optional messages or a
        system message. If both 'messages' (a list of ChatMessageContent instances) and 'system_message' are
        provided, the 'system_message' is prepended to the list of messages, ensuring it appears as the first
        message in the history. If only 'system_message' is provided without any 'messages', the chat history is
        initialized with the 'system_message' as its first item. If 'messages' are provided without a
        'system_message', the chat history is initialized with the provided messages as is.

        Parameters:
        - **data: Arbitrary keyword arguments. The constructor looks for two optional keys:
            - 'messages': list[ChatMessageContent] | None, a list of chat messages to include in the history.
            - 'system_message' str | None: An optional string representing a system-generated message to be
                included at the start of the chat history.

        Note: The 'system_message' is not retained as part of the class's attributes; it's used during
        initialization and then discarded. The rest of the keyword arguments are passed to the superclass
        constructor and handled according to the Pydantic model's behavior.
        """
        system_message_content = data.pop("system_message", None)
        message_type = data.get("message_type", CHAT_MESSAGE_CONTENT)

        if system_message_content:
            system_message = ChatMessageContentBase.from_fields(
                role=ChatRole.SYSTEM, content=system_message_content, type=message_type
            )

            if "messages" in data:
                data["messages"] = [system_message] + data["messages"]
            else:
                data["messages"] = [system_message]
        if "messages" not in data:
            data["messages"] = []
        super().__init__(**data)

    def add_system_message(self, content: str, **kwargs: Any) -> None:
        """Add a system message to the chat history."""
        self.add_message(message=self._prepare_for_add(ChatRole.SYSTEM, content, **kwargs))

    def add_user_message(self, content: str, **kwargs: Any) -> None:
        """Add a user message to the chat history."""
        self.add_message(message=self._prepare_for_add(ChatRole.USER, content, **kwargs))

    def add_assistant_message(self, content: str, **kwargs: Any) -> None:
        """Add an assistant message to the chat history."""
        self.add_message(message=self._prepare_for_add(ChatRole.ASSISTANT, content, **kwargs))

    def add_tool_message(
        self, content: str | None = None, metadata: dict[str, Any] | None = None, **kwargs: Any
    ) -> None:
        """Add a tool message to the chat history."""
        self.add_message(message=self._prepare_for_add(ChatRole.TOOL, content, **kwargs), metadata=metadata)

    def add_message(
        self,
        message: "ChatMessageContent" | dict[str, Any],
        encoding: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Add a message to the history.

        This method accepts either a ChatMessageContent instance or a
        dictionary with the necessary information to construct a ChatMessageContent instance.

        Args:
            message (ChatMessageContent | dict): The message to add, either as
                a pre-constructed ChatMessageContent instance or a dictionary specifying 'role' and 'content'.
            encoding (str | None): The encoding of the message. Required if 'message' is a dict.
            metadata (dict[str, Any] | None): Any metadata to attach to the message. Required if 'message' is a dict.
        """
        from semantic_kernel.contents.chat_message_content import ChatMessageContent

        if isinstance(message, ChatMessageContent):
            self.messages.append(message)
            return
        if "role" not in message:
            raise ContentInitializationError(f"Dictionary must contain at least the role. Got: {message}")
        if encoding:
            message["encoding"] = encoding
        if metadata:
            message["metadata"] = metadata
        if "type" not in message:
            message["type"] = self.message_type
        self.messages.append(ChatMessageContentBase.from_dict(message))

    def _prepare_for_add(self, role: ChatRole, content: str | None = None, **kwargs: Any) -> dict[str, str]:
        """Prepare a message to be added to the history."""
        kwargs["role"] = role
        kwargs["content"] = content
        return kwargs

    def remove_message(self, message: "ChatMessageContent") -> bool:
        """Remove a message from the history.

        Args:
            message (ChatMessageContent): The message to remove.

        Returns:
            bool: True if the message was removed, False if the message was not found.
        """
        try:
            self.messages.remove(message)
            return True
        except ValueError:
            return False

    def __len__(self) -> int:
        """Return the number of messages in the history."""
        return len(self.messages)

    def __getitem__(self, index: int) -> "ChatMessageContent":
        """Get a message from the history using the [] operator.

        Args:
            index (int): The index of the message to get.

        Returns:
            ChatMessageContent: The message at the specified index.
        """
        return self.messages[index]

    def __contains__(self, item: "ChatMessageContent") -> bool:
        """Check if a message is in the history.

        Args:
            item (ChatMessageContent): The message to check for.

        Returns:
            bool: True if the message is in the history, False otherwise.
        """
        return item in self.messages

    def __str__(self) -> str:
        """Return a string representation of the history."""
        chat_history_xml = Element(ROOT_KEY_HISTORY)
        for message in self.messages:
            chat_history_xml.append(message.to_element(root_key=ROOT_KEY_MESSAGE))
        return tostring(chat_history_xml, encoding="unicode", short_empty_elements=True)

    def __iter__(self) -> Iterator["ChatMessageContent"]:
        """Return an iterator over the messages in the history."""
        return iter(self.messages)

    def __eq__(self, other: Any) -> bool:
        """Check if two ChatHistory instances are equal."""
        if not isinstance(other, ChatHistory):
            return False

        return self.messages == other.messages

    @classmethod
    def from_rendered_prompt(cls, rendered_prompt: str, message_type: str = CHAT_MESSAGE_CONTENT) -> "ChatHistory":
        """
        Create a ChatHistory instance from a rendered prompt.

        Args:
            rendered_prompt (str): The rendered prompt to convert to a ChatHistory instance.

        Returns:
            ChatHistory: The ChatHistory instance created from the rendered prompt.
        """
        messages: List[ChatMessageContent] = []
        prompt = rendered_prompt.strip()
        try:
            xml_prompt = XML(text=f"<prompt>{prompt}</prompt>")
        except ParseError:
            logger.info(f"Could not parse prompt {prompt} as xml, treating as text")
            return cls(
                messages=[ChatMessageContentBase.from_fields(role=ChatRole.USER, content=prompt, type=message_type)]
            )
        if xml_prompt.text and xml_prompt.text.strip():
            messages.append(
                ChatMessageContentBase.from_fields(
                    role=ChatRole.SYSTEM, content=xml_prompt.text.strip(), type=message_type
                )
            )
        for item in xml_prompt:
            if item.tag == ROOT_KEY_MESSAGE:
                messages.append(ChatMessageContentBase.from_element(item))
            elif item.tag == ROOT_KEY_HISTORY:
                for message in item:
                    messages.append(ChatMessageContentBase.from_element(message))
            if item.tail and item.tail.strip():
                messages.append(
                    ChatMessageContentBase.from_fields(role=ChatRole.USER, content=item.tail.strip(), type=message_type)
                )
        if len(messages) == 1 and messages[0].role == ChatRole.SYSTEM:
            messages[0].role = ChatRole.USER
        return cls(messages=messages, message_type=message_type)

    def serialize(self) -> str:
        """
        Serializes the ChatHistory instance to a JSON string.

        Returns:
            str: A JSON string representation of the ChatHistory instance.

        Raises:
            ValueError: If the ChatHistory instance cannot be serialized to JSON.
        """
        try:
            return self.model_dump_json(indent=4, exclude_none=True)
        except Exception as e:
            raise ContentSerializationError(f"Unable to serialize ChatHistory to JSON: {e}") from e

    @classmethod
    def restore_chat_history(cls, chat_history_json: str) -> "ChatHistory":
        """
        Restores a ChatHistory instance from a JSON string.

        Args:
            chat_history_json (str): The JSON string to deserialize
                into a ChatHistory instance.

        Returns:
            ChatHistory: The deserialized ChatHistory instance.

        Raises:
            ValueError: If the JSON string is invalid or the deserialized data
                fails validation.
        """
        try:
            return ChatHistory.model_validate_json(chat_history_json)
        except Exception as e:
            raise ContentInitializationError(f"Invalid JSON format: {e}")

    def store_chat_history_to_file(self, file_path: str) -> None:
        """
        Stores the serialized ChatHistory to a file.

        Args:
            file_path (str): The path to the file where the serialized data will be stored.
        """
        json_str = self.serialize()
        with open(file_path, "w") as file:
            file.write(json_str)

    @classmethod
    def load_chat_history_from_file(cls, file_path: str) -> "ChatHistory":
        """
        Loads the ChatHistory from a file.

        Args:
            file_path (str): The path to the file from which to load the ChatHistory.

        Returns:
            ChatHistory: The deserialized ChatHistory instance.
        """
        with open(file_path, "r") as file:
            json_str = file.read()
        return cls.restore_chat_history(json_str)
