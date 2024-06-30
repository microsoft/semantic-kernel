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
    BINARY_CONTENT = BINARY_CONTENT_TAG
    CHAT_MESSAGE_CONTENT = CHAT_MESSAGE_CONTENT_TAG
    IMAGE_CONTENT = IMAGE_CONTENT_TAG
    FUNCTION_CALL_CONTENT = FUNCTION_CALL_CONTENT_TAG
    FUNCTION_RESULT_CONTENT = FUNCTION_RESULT_CONTENT_TAG
    TEXT_CONTENT = TEXT_CONTENT_TAG
