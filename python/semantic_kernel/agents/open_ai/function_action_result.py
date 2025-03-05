# Copyright (c) Microsoft. All rights reserved.

import logging
from dataclasses import dataclass

from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.utils.experimental_decorator import experimental_class

logger: logging.Logger = logging.getLogger(__name__)


@experimental_class
@dataclass
class FunctionActionResult:
    """Function Action Result."""

    function_call_content: ChatMessageContent | None
    function_result_content: ChatMessageContent | None
    tool_outputs: list[dict[str, str]] | None
