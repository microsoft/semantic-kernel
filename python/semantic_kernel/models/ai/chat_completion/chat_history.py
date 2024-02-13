# Copyright (c) Microsoft. All rights reserved.

from typing import Iterator, List, Optional

from pydantic import Field

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
        system_message = data.pop("system_message", None)

        super().__init__(**data)

        if system_message:
            self.add_system_message(system_message)

    def add_system_message(self, content: str) -> None:
        """Add a system message to the chat template."""
        self.add_message(ChatRole.SYSTEM, content)

    def add_user_message(self, content: str) -> None:
        """Add a user message to the chat template."""
        self.add_message(ChatRole.USER, content)

    def add_assistant_message(self, content: str) -> None:
        """Add an assistant message to the chat template."""
        self.add_message(ChatRole.ASSISTANT, content)

    def add_tool_message(self, content: str) -> None:
        """Add a tool message to the chat template."""
        self.add_message(ChatRole.TOOL, content)

    def add_message(self, role: ChatRole, content: str, encoding: Optional[str] = None) -> None:
        """Add a message to the history.

        Args:
            role (ChatRole): The role of the message (user, assistant, system, or tool).
            message (ChatMessageContent): The message to add.
            encoding (Optional[str]): The encoding of the message.
        """
        self.messages.append(ChatMessageContent(role=role, content=content, encoding=encoding))

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

    def __iter__(self) -> Iterator[ChatMessageContent]:
        return iter(self.messages)
    
    #TODO Add restore?
    #@classmethod
    # def restore(
    #     cls,
    #     messages: List[Dict[str, str]],
    #     template: str,
    #     template_engine: PromptTemplatingEngine,
    #     prompt_config: PromptTemplateConfig,
    #     parse_chat_system_prompt: bool = False,
    #     parse_messages: bool = False,
    #     **kwargs: Any,
    # )
