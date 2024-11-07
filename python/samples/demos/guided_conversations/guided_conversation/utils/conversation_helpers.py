# Copyright (c) Microsoft. All rights reserved.

from dataclasses import dataclass, field
import datetime
from enum import Enum
import logging
from typing import Union

from semantic_kernel.contents import ChatMessageContent


class ConversationMessageType(Enum):
    DEFAULT = "default"
    ARTIFACT_UPDATE = "artifact-update"
    REASONING = "reasoning"


@dataclass
class Conversation:
    """An abstraction to represent a list of messages and common operations such as adding messages
    and getting a string representation.

    Args:
        conversation_messages (list[ChatMessageContent]): A list of ChatMessageContent objects.
    """

    logger = logging.getLogger(__name__)
    conversation_messages: list[ChatMessageContent] = field(default_factory=list)

    def add_messages(self, messages: Union[ChatMessageContent, list[ChatMessageContent], "Conversation", None]) -> None:
        """Add a message, list of messages to the conversation or merge another conversation into the end of this one.

        Args:
            messages (Union[ChatMessageContent, list[ChatMessageContent], "Conversation"]): The message(s) to add.
                All messages will be added to the end of the conversation.

        Returns:
            None
        """
        if isinstance(messages, list):
            self.conversation_messages.extend(messages)
        elif isinstance(messages, Conversation):
            self.conversation_messages.extend(messages.conversation_messages)
        elif isinstance(messages, ChatMessageContent):
            # if ChatMessageContent.metadata doesn't have type, then add default
            if "type" not in messages.metadata:
                messages.metadata["type"] = ConversationMessageType.DEFAULT
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
                message
                for message in self.conversation_messages
                if "type" in message.metadata and message.metadata["type"] not in exclude_types
            ]
        else:
            conversation_messages = self.conversation_messages

        to_join = []
        current_turn = None
        for message in conversation_messages:
            participant_name = message.name
            # Modify the default user to be capitalized for consistency with how assistant is written.
            if participant_name == "user":
                participant_name = "User"

            # If the turn number is None, don't include it in the string
            if "turn_number" in message.metadata and current_turn != message.metadata["turn_number"]:
                current_turn = message.metadata["turn_number"]
                to_join.append(f"[Turn {current_turn}]")

            # Add the message content
            if (message.role == "assistant") and (
                "type" in message.metadata and message.metadata["type"] == ConversationMessageType.ARTIFACT_UPDATE
            ):
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
            message.metadata["turn_number"] = turn_number

    @staticmethod
    def message_to_json(message: ChatMessageContent) -> dict:
        """
        Convert a ChatMessageContent object to a JSON serializable dictionary.

        Args:
            message (ChatMessageContent): The ChatMessageContent object to convert to JSON.

        Returns:
            dict: A JSON serializable dictionary representation of the ChatMessageContent object.
        """
        return {
            "role": message.role,
            "content": message.content,
            "name": message.name,
            "metadata": {
                "turn_number": message.metadata.get("turn_number", None),
                "type": message.metadata.get("type", ConversationMessageType.DEFAULT),
            },
        }

    def to_json(self) -> dict:
        json_data = {}
        json_data["conversation"] = {}
        json_data["conversation"]["conversation_messages"] = [
            self.message_to_json(message) for message in self.conversation_messages
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
                ChatMessageContent(
                    role=message["role"],
                    content=message["content"],
                    name=message["name"],
                    metadata={
                        "turn_number": message["turn_number"],
                        "type": ConversationMessageType(message["type"]),
                        "timestamp": datetime.datetime.fromisoformat(message["timestamp"]),
                    },
                )
            )

        return conversation
