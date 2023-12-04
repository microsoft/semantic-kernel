# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import TYPE_CHECKING, List, Optional, TypeVar

from semantic_kernel.models.chat.chat_message import ChatMessage
from semantic_kernel.semantic_functions.chat_prompt_template import ChatPromptTemplate
from semantic_kernel.semantic_functions.prompt_template_config import (
    PromptTemplateConfig,
)
from semantic_kernel.template_engine.protocols.prompt_templating_engine import (
    PromptTemplatingEngine,
)


ChatMessageT = TypeVar("ChatMessageT", bound=ChatMessage)


class ChatWithDataPromptTemplate(ChatPromptTemplate):
    _messages: List[ChatMessageT]

    def __init__(
        self,
        template: str,
        template_engine: PromptTemplatingEngine,
        prompt_config: PromptTemplateConfig,
        log: Optional[Logger] = None,
    ) -> None:
        super().__init__(template, template_engine, prompt_config, log)

    def add_tool_message(self, message: str) -> None:
        """Add an assistant message to the chat template."""
        super().add_message("tool", message)
