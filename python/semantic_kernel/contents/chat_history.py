# Copyright (c) Microsoft. All rights reserved.

import logging
from collections.abc import Generator
from functools import singledispatchmethod
from html import unescape
from typing import Any
from xml.etree.ElementTree import Element, tostring  # nosec

from defusedxml.ElementTree import XML, ParseError
from pydantic import field_validator

from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.const import CHAT_HISTORY_TAG, CHAT_MESSAGE_CONTENT_TAG
from semantic_kernel.contents.kernel_content import KernelContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions import ContentInitializationError, ContentSerializationError
from semantic_kernel.kernel_pydantic import KernelBaseModel

logger = logging.getLogger(__name__)


class ChatHistory(KernelBaseModel):
    """This class holds the history of chat messages from a chat conversation.

    Note: the constructor takes a system_message parameter, which is not part
    of the class definition. This is to allow the system_message to be passed in
    as a keyword argument, but not be part of the class definition.

    Attributes:
        messages (List[ChatMessageContent]): The list of chat messages in the history.
    """

    messages: list[ChatMessageContent]

    def __init__(self, **data: Any):
        """Initializes a new instance of the ChatHistory class.

        Optionally incorporating a message and/or a system message at the beginning of the chat history.

        This constructor allows for flexible initialization with chat messages and an optional messages or a
        system message. If both 'messages' (a list of ChatMessageContent instances) and 'system_message' are
        provided, the 'system_message' is prepended to the list of messages, ensuring it appears as the first
        message in the history. If only 'system_message' is provided without any 'messages', the chat history is
        initialized with the 'system_message' as its first item. If 'messages' are provided without a
        'system_message', the chat history is initialized with the provided messages as is.

        Note: The 'system_message' is not retained as part of the class's attributes; it's used during
        initialization and then discarded. The rest of the keyword arguments are passed to the superclass
        constructor and handled according to the Pydantic model's behavior.

        Args:
            **data: Arbitrary keyword arguments.
                The constructor looks for two optional keys:
                - 'messages': Optional[List[ChatMessageContent]], a list of chat messages to include in the history.
                - 'system_message' Optional[str]: An optional string representing a system-generated message to be
                    included at the start of the chat history.

        """
        system_message_content = data.pop("system_message", None)

        if system_message_content:
            system_message = ChatMessageContent(role=AuthorRole.SYSTEM, content=system_message_content)

            if "messages" in data:
                data["messages"] = [system_message] + data["messages"]
            else:
                data["messages"] = [system_message]
        if "messages" not in data:
            data["messages"] = []
        super().__init__(**data)

    @field_validator("messages", mode="before")
    @classmethod
    def _validate_messages(cls, messages: list[ChatMessageContent]) -> list[ChatMessageContent]:
        if not messages:
            return messages
        out_msgs: list[ChatMessageContent] = []
        for message in messages:
            if isinstance(message, dict):
                out_msgs.append(ChatMessageContent.model_validate(message))
            else:
                out_msgs.append(message)
        return out_msgs

    @singledispatchmethod
    def add_system_message(self, content: str | list[KernelContent], **kwargs) -> None:
        """Add a system message to the chat history."""
        raise NotImplementedError

    @add_system_message.register
    def add_system_message_str(self, content: str, **kwargs: Any) -> None:
        """Add a system message to the chat history."""
        self.add_message(message=self._prepare_for_add(role=AuthorRole.SYSTEM, content=content, **kwargs))

    @add_system_message.register(list)
    def add_system_message_list(self, content: list[KernelContent], **kwargs: Any) -> None:
        """Add a system message to the chat history."""
        self.add_message(message=self._prepare_for_add(role=AuthorRole.SYSTEM, items=content, **kwargs))

    @singledispatchmethod
    def add_user_message(self, content: str | list[KernelContent], **kwargs: Any) -> None:
        """Add a user message to the chat history."""
        raise NotImplementedError

    @add_user_message.register
    def add_user_message_str(self, content: str, **kwargs: Any) -> None:
        """Add a user message to the chat history."""
        self.add_message(message=self._prepare_for_add(role=AuthorRole.USER, content=content, **kwargs))

    @add_user_message.register(list)
    def add_user_message_list(self, content: list[KernelContent], **kwargs: Any) -> None:
        """Add a user message to the chat history."""
        self.add_message(message=self._prepare_for_add(role=AuthorRole.USER, items=content, **kwargs))

    @singledispatchmethod
    def add_assistant_message(self, content: str | list[KernelContent], **kwargs: Any) -> None:
        """Add an assistant message to the chat history."""
        raise NotImplementedError

    @add_assistant_message.register
    def add_assistant_message_str(self, content: str, **kwargs: Any) -> None:
        """Add an assistant message to the chat history."""
        self.add_message(message=self._prepare_for_add(role=AuthorRole.ASSISTANT, content=content, **kwargs))

    @add_assistant_message.register(list)
    def add_assistant_message_list(self, content: list[KernelContent], **kwargs: Any) -> None:
        """Add an assistant message to the chat history."""
        self.add_message(message=self._prepare_for_add(role=AuthorRole.ASSISTANT, items=content, **kwargs))

    @singledispatchmethod
    def add_tool_message(self, content: str | list[KernelContent], **kwargs: Any) -> None:
        """Add a tool message to the chat history."""
        raise NotImplementedError

    @add_tool_message.register
    def add_tool_message_str(self, content: str, **kwargs: Any) -> None:
        """Add a tool message to the chat history."""
        self.add_message(message=self._prepare_for_add(role=AuthorRole.TOOL, content=content, **kwargs))

    @add_tool_message.register(list)
    def add_tool_message_list(self, content: list[KernelContent], **kwargs: Any) -> None:
        """Add a tool message to the chat history."""
        self.add_message(message=self._prepare_for_add(role=AuthorRole.TOOL, items=content, **kwargs))

    def add_message(
        self,
        message: ChatMessageContent | dict[str, Any],
        encoding: str | None = None,
        metadata: dict[str, Any] | None = None,
    ) -> None:
        """Add a message to the history.

        This method accepts either a ChatMessageContent instance or a
        dictionary with the necessary information to construct a ChatMessageContent instance.

        Args:
            message (Union[ChatMessageContent, dict]): The message to add, either as
                a pre-constructed ChatMessageContent instance or a dictionary specifying 'role' and 'content'.
            encoding (Optional[str]): The encoding of the message. Required if 'message' is a dict.
            metadata (Optional[dict[str, Any]]): Any metadata to attach to the message. Required if 'message' is a dict.
        """
        if isinstance(message, ChatMessageContent):
            self.messages.append(message)
            return
        if "role" not in message:
            raise ContentInitializationError(f"Dictionary must contain at least the role. Got: {message}")
        if encoding:
            message["encoding"] = encoding
        if metadata:
            message["metadata"] = metadata
        self.messages.append(ChatMessageContent(**message))

    def _prepare_for_add(
        self, role: AuthorRole, content: str | None = None, items: list[KernelContent] | None = None, **kwargs: Any
    ) -> dict[str, str]:
        """Prepare a message to be added to the history."""
        kwargs["role"] = role
        if content:
            kwargs["content"] = content
        if items:
            kwargs["items"] = items
        return kwargs

    def remove_message(self, message: ChatMessageContent) -> bool:
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

    def __getitem__(self, index: int) -> ChatMessageContent:
        """Get a message from the history using the [] operator.

        Args:
            index (int): The index of the message to get.

        Returns:
            ChatMessageContent: The message at the specified index.
        """
        return self.messages[index]

    def __contains__(self, item: ChatMessageContent) -> bool:
        """Check if a message is in the history.

        Args:
            item (ChatMessageContent): The message to check for.

        Returns:
            bool: True if the message is in the history, False otherwise.
        """
        return item in self.messages

    def __str__(self) -> str:
        """Return a string representation of the history."""
        chat_history_xml = Element(CHAT_HISTORY_TAG)
        for message in self.messages:
            chat_history_xml.append(message.to_element())
        return tostring(chat_history_xml, encoding="unicode", short_empty_elements=True)

    def to_prompt(self) -> str:
        """Return a string representation of the history."""
        chat_history_xml = Element(CHAT_HISTORY_TAG)
        for message in self.messages:
            chat_history_xml.append(message.to_element())
        return tostring(chat_history_xml, encoding="unicode", short_empty_elements=True)

    def __iter__(self) -> Generator[ChatMessageContent, None, None]:  # type: ignore
        """Return an iterator over the messages in the history."""
        yield from self.messages

    def __eq__(self, other: Any) -> bool:
        """Check if two ChatHistory instances are equal."""
        if not isinstance(other, ChatHistory):
            return False

        return self.messages == other.messages

    @classmethod
    def from_rendered_prompt(cls, rendered_prompt: str) -> "ChatHistory":
        """Create a ChatHistory instance from a rendered prompt.

        Args:
            rendered_prompt (str): The rendered prompt to convert to a ChatHistory instance.

        Returns:
            ChatHistory: The ChatHistory instance created from the rendered prompt.
        """
        prompt_tag = "root"
        messages: list["ChatMessageContent"] = []
        prompt = rendered_prompt.strip()
        try:
            xml_prompt = XML(text=f"<{prompt_tag}>{prompt}</{prompt_tag}>")
        except ParseError as exc:
            logger.info(f"Could not parse prompt {prompt} as xml, treating as text, error was: {exc}")
            return cls(messages=[ChatMessageContent(role=AuthorRole.USER, content=unescape(prompt))])
        if xml_prompt.text and xml_prompt.text.strip():
            messages.append(ChatMessageContent(role=AuthorRole.SYSTEM, content=unescape(xml_prompt.text.strip())))
        for item in xml_prompt:
            if item.tag == CHAT_MESSAGE_CONTENT_TAG:
                messages.append(ChatMessageContent.from_element(item))
            elif item.tag == CHAT_HISTORY_TAG:
                for message in item:
                    messages.append(ChatMessageContent.from_element(message))
            if item.tail and item.tail.strip():
                messages.append(ChatMessageContent(role=AuthorRole.USER, content=unescape(item.tail.strip())))
        if len(messages) == 1 and messages[0].role == AuthorRole.SYSTEM:
            messages[0].role = AuthorRole.USER
        return cls(messages=messages)

    def serialize(self) -> str:
        """Serializes the ChatHistory instance to a JSON string.

        Returns:
            str: A JSON string representation of the ChatHistory instance.

        Raises:
            ValueError: If the ChatHistory instance cannot be serialized to JSON.
        """
        try:
            return self.model_dump_json(indent=2, exclude_none=True)
        except Exception as e:  # pragma: no cover
            raise ContentSerializationError(f"Unable to serialize ChatHistory to JSON: {e}") from e

    @classmethod
    def restore_chat_history(cls, chat_history_json: str) -> "ChatHistory":
        """Restores a ChatHistory instance from a JSON string.

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
        """Stores the serialized ChatHistory to a file.

        Args:
            file_path (str): The path to the file where the serialized data will be stored.
        """
        json_str = self.serialize()
        with open(file_path, "w") as file:
            file.write(json_str)

    @classmethod
    def load_chat_history_from_file(cls, file_path: str) -> "ChatHistory":
        """Loads the ChatHistory from a file.

        Args:
            file_path (str): The path to the file from which to load the ChatHistory.

        Returns:
            ChatHistory: The deserialized ChatHistory instance.
        """
        with open(file_path) as file:
            json_str = file.read()
        return cls.restore_chat_history(json_str)
