# Copyright (c) Microsoft. All rights reserved.

from typing import Union

from typing_extensions import deprecated

from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.image_content import ImageContent
from semantic_kernel.contents.streaming_text_content import StreamingTextContent

ITEM_TYPES = Union[
    ImageContent,
    StreamingTextContent,
    FunctionCallContent,
    FunctionResultContent,
]


@deprecated("StreamingChatMessageContent is deprecated. Use ChatMessageContent instead.")
class StreamingChatMessageContent(ChatMessageContent):
    """This represents a streaming chat message response content.

    This class is deprecated in favor of ChatMessageContent for simplicity.
    """

    pass
