# Copyright (c) Microsoft. All rights reserved.

import asyncio
from logging import Logger
from typing import TYPE_CHECKING, Dict, List, Optional

from semantic_kernel.models.chat.chat_message import ChatMessage
from semantic_kernel.models.usage_result import UsageResult
from semantic_kernel.semantic_functions.prompt_template import PromptTemplate
from semantic_kernel.semantic_functions.prompt_template_config import (
    PromptTemplateConfig,
)
from semantic_kernel.template_engine.protocols.prompt_templating_engine import (
    PromptTemplatingEngine,
)

if TYPE_CHECKING:
    from semantic_kernel.orchestration.sk_context import SKContext


# TODO: rename to ChatHistory
class ChatPromptTemplate(PromptTemplate):
    _messages: List[ChatMessage]
    _usage: UsageResult = UsageResult()

    def __init__(
        self,
        template: str,
        template_engine: PromptTemplatingEngine,
        prompt_config: PromptTemplateConfig,
        log: Optional[Logger] = None,
    ) -> None:
        super().__init__(template, template_engine, prompt_config, log)
        self._messages = []

    async def render_async(self, context: "SKContext") -> str:
        raise NotImplementedError(
            "Can't call render_async on a ChatPromptTemplate.\n"
            "Use render_messages_async instead."
        )

    def add_system_message(self, message: str, name: Optional[str] = None) -> None:
        self.add_message("system", message, name)

    def add_user_message(self, message: str, name: Optional[str] = None) -> None:
        self.add_message("user", message, name)

    def add_assistant_message(self, message: str, name: Optional[str] = None) -> None:
        self.add_message("assistant", message, name)

    def add_message(self, role: str, message: str, name: Optional[str] = None) -> None:
        self._messages.append(
            ChatMessage(
                role=role,
                content_template=PromptTemplate(
                    message, self._template_engine, self._prompt_config
                ),
                name=name,
            )
        )

    def add_chat_message(self, chat_message: ChatMessage) -> None:
        self._messages.append(chat_message)

    async def render_messages_async(self, context: "SKContext") -> List[Dict[str, str]]:
        self.add_message(role="user", message=self._template)
        await asyncio.gather(
            *[message.render_message_async(context) for message in self._messages]
        )
        return [message.as_dict() for message in self._messages]

    @property
    def latest(self) -> Optional[ChatMessage]:
        if len(self._messages) == 0:
            return None
        return self._messages[-1]

    @property
    def usage(self) -> UsageResult:
        return self._usage

    def add_usage(self, usage: UsageResult) -> None:
        self._usage += usage
