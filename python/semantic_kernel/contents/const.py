# Copyright (c) Microsoft. All rights reserved.

from typing import Final, Literal, Union

ROOT_KEY_MESSAGE: Final[str] = "message"
ROOT_KEY_HISTORY: Final[str] = "chat_history"
AZURE_CHAT_MESSAGE_CONTENT: Final[str] = "AzureChatMessageContent"
OPENAI_CHAT_MESSAGE_CONTENT: Final[str] = "OpenAIChatMessageContent"
CHAT_MESSAGE_CONTENT: Final[str] = "ChatMessageContent"

ALL_CHAT_MESSAGE_CONTENTS = Union[CHAT_MESSAGE_CONTENT, OPENAI_CHAT_MESSAGE_CONTENT, AZURE_CHAT_MESSAGE_CONTENT]
TYPES_CHAT_MESSAGE_CONTENT = Literal[CHAT_MESSAGE_CONTENT, OPENAI_CHAT_MESSAGE_CONTENT, AZURE_CHAT_MESSAGE_CONTENT]
