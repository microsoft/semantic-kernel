# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import Any, Dict, List, Optional

from semantic_kernel.connectors.ai.open_ai.models.chat.function_call import FunctionCall
from semantic_kernel.connectors.ai.open_ai.models.chat.open_ai_chat_message import (
    OpenAIChatMessage,
)
from semantic_kernel.connectors.ai.open_ai.semantic_functions.open_ai_chat_prompt_template import OpenAIChatPromptTemplate
from semantic_kernel.semantic_functions.chat_prompt_template import ChatPromptTemplate
from semantic_kernel.semantic_functions.chat_with_data_prompt_template import ChatWithDataPromptTemplate
from semantic_kernel.semantic_functions.prompt_template import PromptTemplate
from semantic_kernel.semantic_functions.prompt_template_config import (
    PromptTemplateConfig,
)
from semantic_kernel.template_engine.protocols.prompt_templating_engine import (
    PromptTemplatingEngine,
)


class AzureChatWithDataPromptTemplate(OpenAIChatPromptTemplate, ChatWithDataPromptTemplate):
    def add_tool_message(self, message: str) -> None:
        """Add a tool message to the chat template."""
        super().add_message("tool", message)
