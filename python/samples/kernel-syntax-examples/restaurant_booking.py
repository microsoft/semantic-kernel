# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os
from functools import reduce
from typing import TYPE_CHECKING, Any, Dict, List, Union

import semantic_kernel as sk
import semantic_kernel.connectors.ai.open_ai as sk_oai
from semantic_kernel.connectors.ai.open_ai.contents.open_ai_chat_message_content import \
    OpenAIChatMessageContent
from semantic_kernel.connectors.ai.open_ai.contents.open_ai_streaming_chat_message_content import \
    OpenAIStreamingChatMessageContent
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import \
    OpenAIPromptExecutionSettings
from semantic_kernel.connectors.ai.open_ai.utils import get_tool_call_object
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.core_plugins import MathPlugin, TimePlugin
from semantic_kernel.functions.kernel_arguments import KernelArguments

if TYPE_CHECKING:
    from semantic_kernel.functions.kernel_function import KernelFunction

