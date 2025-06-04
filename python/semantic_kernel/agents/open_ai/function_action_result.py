# Copyright (c) Microsoft. All rights reserved.

import logging
from dataclasses import dataclass

from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.utils.feature_stage_decorator import experimental

logger: logging.Logger = logging.getLogger(__name__)


@experimental
@dataclass
class FunctionActionResult:
    """Function Action Result."""

    function_call_streaming_content: StreamingChatMessageContent
    function_result_streaming_content: StreamingChatMessageContent
    tool_outputs: list[dict[str, str]]
