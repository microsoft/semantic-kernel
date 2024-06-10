# Copyright (c) Microsoft. All rights reserved.
from enum import Enum
from typing import Final

CHAT_MESSAGE_CONTENT_TAG: Final[str] = "message"
CHAT_HISTORY_TAG: Final[str] = "chat_history"
TEXT_CONTENT_TAG: Final[str] = "text"
IMAGE_CONTENT_TAG: Final[str] = "image"
BINARY_CONTENT_TAG: Final[str] = "binary"
FUNCTION_CALL_CONTENT_TAG: Final[str] = "function_call"
FUNCTION_RESULT_CONTENT_TAG: Final[str] = "function_result"
DISCRIMINATOR_FIELD: Final[str] = "content_type"


class ContentTypes(str, Enum):
    BINARY_CONTENT = "binary"
    CHAT_MESSAGE_CONTENT = "message"
    IMAGE_CONTENT = "image"
    FUNCTION_CALL_CONTENT = "function_call"
    FUNCTION_RESULT_CONTENT = "function_result"
    TEXT_CONTENT = "text"
