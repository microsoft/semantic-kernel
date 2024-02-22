# Copyright (c) Microsoft. All rights reserved.

import json
import xml.etree.ElementTree as ET
from typing import Any, Iterator, List, Optional, Tuple, Union

from pydantic import Field, ValidationError
from pydantic.json import pydantic_encoder
from pydantic.tools import parse_obj_as

from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.models.ai.chat_completion.chat_role import ChatRole


class ChatHistory(KernelBaseModel):
    """
    This class holds the history of chat messages from a chat conversation.

    Note: the constructor takes a system_message parameter, which is not part
    of the class definition. This is to allow the system_message to be passed in
    as a keyword argument, but not be part of the class definition.

    Attributes:
        messages (List[ChatMessageContent]): The list of chat messages in the history.
    """

    messages: Optional[List[ChatMessageContent]] = Field(default_factory=list)

    def __init__(self, **data):
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
            - 'messages': Optional[List[ChatMessageContent]], a list of chat messages to include in the history.
            - 'system_message' Optional[str]: An optional string representing a system-generated message to be
                included at the start of the chat history.

        Note: The 'system_message' is not retained as part of the class's attributes; it's used during
        initialization and then discarded. The rest of the keyword arguments are passed to the superclass
        constructor and handled according to the Pydantic model's behavior.
        """
        system_message_content = data.pop("system_message", None)

        if system_message_content:
            system_message = ChatMessageContent(role=ChatRole.SYSTEM, content=system_message_content)

            if "messages" in data:
                data["messages"] = [system_message] + data["messages"]
            else:
                data["messages"] = [system_message]

        super().__init__(**data)

    def add_system_message(self, content: str) -> None:
        """Add a system message to the chat history."""
        self.add_message(message=self._prepare_for_add(ChatRole.SYSTEM, content))

    def add_user_message(self, content: str) -> None:
        """Add a user message to the chat history."""
        self.add_message(message=self._prepare_for_add(ChatRole.USER, content))

    def add_assistant_message(self, content: str) -> None:
        """Add an assistant message to the chat history."""
        self.add_message(message=self._prepare_for_add(ChatRole.ASSISTANT, content))

    def add_tool_message(self, content: str, metadata: Optional[dict[str, Any]] = None) -> None:
        """Add a tool message to the chat history."""
        self.add_message(message=self._prepare_for_add(ChatRole.TOOL, content), metadata=metadata)

    def add_message(
        self,
        message: Union[ChatMessageContent, dict],
        encoding: Optional[str] = None,
        metadata: Optional[dict[str, Any]] = None,
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
            chat_message = message
        elif isinstance(message, dict):
            required_keys = {"role", "content"}
            if not required_keys.issubset(message.keys()):
                raise ValueError(f"Dictionary must contain the following keys: {required_keys}")
            chat_message = ChatMessageContent(
                role=message["role"], content=message["content"], encoding=encoding, metadata=metadata
            )
        else:
            raise TypeError("message must be an instance of ChatMessageContent or a dictionary")

        self.messages.append(chat_message)

    def _prepare_for_add(self, role: ChatRole, content: str) -> dict[str, str]:
        """Prepare a message to be added to the history."""
        return {"role": role, "content": content}

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
        if not self.messages:
            return "<>"
        return "\n".join([msg.to_prompt() for msg in self.messages])

    def __iter__(self) -> Iterator[ChatMessageContent]:
        """Return an iterator over the messages in the history."""
        return iter(self.messages)

    def __eq__(self, other: "ChatHistory") -> bool:
        """Check if two ChatHistory instances are equal."""
        if not isinstance(other, ChatHistory):
            return False

        return self.messages == other.messages

    @classmethod
    def from_rendered_prompt(cls, rendered_prompt: str) -> "ChatHistory":
        """
        Create a ChatHistory instance from a rendered prompt.

        Args:
            rendered_prompt (str): The rendered prompt to convert to a ChatHistory instance.

        Returns:
            ChatHistory: The ChatHistory instance created from the rendered prompt.
        """
        messages: List[ChatMessageContent] = []
        result, remainder = cls._render_remaining(rendered_prompt, True)
        if result:
            messages.append(result)
        while remainder:
            result, remainder = cls._render_remaining(remainder)
            if result:
                messages.append(result)
        return cls(messages=messages)

    @staticmethod
    def _render_remaining(prompt: Optional[str], first: bool = False) -> Tuple[ChatMessageContent, Optional[str]]:
        """Render the remaining messages in the history."""
        if not prompt:
            return None, None
        prompt = prompt.strip()
        start = prompt.find("<message")
        end = prompt.find("</message>")
        if start == -1 or end == -1:
            return ChatMessageContent(role=ChatRole.SYSTEM if first else ChatRole.USER, content=prompt), None
        if start > 0 and end > 0:
            return ChatMessageContent(role=ChatRole.SYSTEM if first else ChatRole.USER, content=prompt[:start]), prompt[
                start:
            ]
        return ChatMessageContent.from_element(ET.fromstring(prompt[start : end + 10])), prompt[end + 10 :]

    def serialize(self) -> str:
        """
        Serializes the ChatHistory instance to a JSON string.

        Returns:
            str: A JSON string representation of the ChatHistory instance.

        Raises:
            ValueError: If the ChatHistory instance cannot be serialized to JSON.
        """
        try:
            return json.dumps(self.model_dump(), indent=4, default=pydantic_encoder)
        except TypeError as e:
            raise ValueError(f"Unable to serialize ChatHistory to JSON: {e}")

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
            history_dict = json.loads(chat_history_json)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")

        try:
            return parse_obj_as(cls, history_dict)
        except ValidationError as e:
            raise ValueError(f"Data validation error during deserialization: {e}")

    def store_chat_history_to_file(chat_history: "ChatHistory", file_path: str) -> None:
        """
        Stores the serialized ChatHistory to a file.

        Args:
            chat_history (ChatHistory): The ChatHistory instance to serialize and store.
            file_path (str): The path to the file where the serialized data will be stored.
        """
        json_str = chat_history.serialize()
        with open(file_path, "w") as file:
            file.write(json_str)

    def load_chat_history_from_file(file_path: str) -> "ChatHistory":
        """
        Loads the ChatHistory from a file.

        Args:
            file_path (str): The path to the file from which to load the ChatHistory.

        Returns:
            ChatHistory: The deserialized ChatHistory instance.
        """
        with open(file_path, "r") as file:
            json_str = file.read()
        return ChatHistory.restore_chat_history(json_str)
