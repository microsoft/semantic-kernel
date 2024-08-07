# Copyright (c) Microsoft. All rights reserved.

from dataclasses import dataclass, field
import datetime
from enum import Enum
import logging
from typing import Literal, Union


class ConversationMessageType(Enum):
    DEFAULT = "default"
    ARTIFACT_UPDATE = "artifact-update"
    REASONING = "reasoning"


@dataclass
class ConversationMessage:
    role: Literal["user", "assistant"]
    content: str
    type: ConversationMessageType = ConversationMessageType.DEFAULT
    participant_name: str | None = None
    turn_number: int | None = None
    timestamp: datetime.datetime = field(default_factory=datetime.datetime.now)

    def __post_init__(self):
        if not self.participant_name:
            if self.role == "user":
                self.participant_name = "user"
            else:
                self.participant_name = "assistant"

    def to_json(self) -> dict:
        json_data = {}
        json_data["role"] = self.role
        json_data["content"] = self.content
        json_data["type"] = self.type.value
        json_data["participant_name"] = self.participant_name
        json_data["turn_number"] = self.turn_number
        json_data["timestamp"] = self.timestamp.isoformat()
        return json_data

    @classmethod
    def from_json(cls, json_data: dict) -> "ConversationMessage":
        return cls(
            role=json_data["role"],
            content=json_data["content"],
            type=ConversationMessageType(json_data["type"]),
            participant_name=json_data["participant_name"],
            turn_number=json_data["turn_number"],
            timestamp=datetime.datetime.fromisoformat(json_data["timestamp"]),
        )


@dataclass
class Conversation:
    """An abstraction to represent a list of messages and common operations such as adding messages
    and getting a string representation.

    Args:
        conversation_messages (list[ConversationMessage]): A list of ConversationMessage objects.
    """

    logger = logging.getLogger(__name__)
    conversation_messages: list[ConversationMessage] = field(default_factory=list)

    def add_messages(
        self, messages: Union[ConversationMessage, list[ConversationMessage], "Conversation", None]
    ) -> None:
        """Add a message, list of messages to the conversation or merge another conversation into the end of this one.

        Args:
            messages (Union[ConversationMessage, list[ConversationMessage], "Conversation"]): The message(s) to add.
                All messages will be added to the end of the conversation.

        Returns:
            None
        """
        if isinstance(messages, list):
            self.conversation_messages.extend(messages)
        elif isinstance(messages, Conversation):
            self.conversation_messages.extend(messages.conversation_messages)
        elif isinstance(messages, ConversationMessage):
            self.conversation_messages.append(messages)
        else:
            self.logger.warning(f"Invalid message type: {type(messages)}")
            return None

    def get_repr_for_prompt(
        self,
        exclude_types: list[ConversationMessageType] | None = None,
    ) -> str:
        """Create a string representation of the conversation history for use in LLM prompts.

        Args:
            exclude_types (list[ConversationMessageType] | None): A list of message types to exclude from the conversation
                history. If None, all message types will be included.

        Returns:
            str: A string representation of the conversation history.
        """
        if len(self.conversation_messages) == 0:
            return "None"

        # Do not include the excluded messages types in the conversation history repr.
        if exclude_types is not None:
            conversation_messages = [
                message for message in self.conversation_messages if message.type not in exclude_types
            ]
        else:
            conversation_messages = self.conversation_messages

        to_join = []
        current_turn = None
        for message in conversation_messages:
            participant_name = message.participant_name
            # Modify the default user to be capitalized for consistency with how assistant is written.
            if participant_name == "user":
                participant_name = "User"

            # If the turn number is None, don't include it in the string
            if current_turn != message.turn_number:
                current_turn = message.turn_number
                to_join.append(f"[Turn {current_turn}]")

            # Add the message content
            if (message.role == "assistant") and (message.type == ConversationMessageType.ARTIFACT_UPDATE):
                to_join.append(message.content)
            elif message.role == "assistant":
                to_join.append(f"Assistant: {message.content}")
            else:
                user_string = message.content.strip()
                if user_string == "":
                    to_join.append(f"{participant_name}: <sent an empty message>")
                else:
                    to_join.append(f"{participant_name}: {user_string}")
        conversation_string = "\n".join(to_join)
        return conversation_string

    def set_turn_numbers(self, turn_number: int) -> None:
        """Set all the turn numbers in the conversation to the given turn number.

        Args:
            turn_number (int): The turn number to set for all messages.

        Returns:
            None"""
        for message in self.conversation_messages:
            message.turn_number = turn_number

    def to_json(self) -> dict:
        json_data = {}
        json_data["conversation"] = {}
        json_data["conversation"]["conversation_messages"] = [
            message.to_json() for message in self.conversation_messages
        ]
        return json_data

    @classmethod
    def from_json(
        cls,
        json_data: dict,
    ) -> "Conversation":
        conversation = cls()
        for message in json_data["conversation"]["conversation_messages"]:
            conversation.add_messages(
                ConversationMessage(
                    role=message["role"],
                    content=message["content"],
                    type=ConversationMessageType(message["type"]),
                    participant_name=message["participant_name"],
                    turn_number=message["turn_number"],
                    timestamp=datetime.datetime.fromisoformat(message["timestamp"]),
                )
            )

        return conversation
