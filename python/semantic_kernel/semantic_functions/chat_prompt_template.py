# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import TYPE_CHECKING, List, Optional, Tuple

from semantic_kernel.semantic_functions.prompt_template import PromptTemplate
from semantic_kernel.semantic_functions.prompt_template_config import (
    PromptTemplateConfig,
)
from semantic_kernel.template_engine.protocols.prompt_templating_engine import (
    PromptTemplatingEngine,
)

if TYPE_CHECKING:
    from semantic_kernel.orchestration.sk_context import SKContext


class ChatPromptTemplate(PromptTemplate):
    _messages: List[Tuple[str, PromptTemplate]]

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

    def add_system_message(self, message: str) -> None:
        self.add_message("system", message)

    def add_user_message(self, message: str) -> None:
        self.add_message("user", message)

    def add_assistant_message(self, message: str) -> None:
        self.add_message("assistant", message)

    def add_message(self, role: str, message: str) -> None:
        self._messages.append(
            (role, PromptTemplate(message, self._template_engine, self._prompt_config))
        )

    async def render_messages_async(
        self, context: "SKContext"
    ) -> List[Tuple[str, str]]:
        rendered_messages = []
        for role, message in self._messages:
            rendered_messages.append((role, await message.render_async(context)))

        latest_user_message = await self._template_engine.render_async(
            self._template, context
        )
        rendered_messages.append(("user", latest_user_message))

        return rendered_messages

    @property
    def messages(self) -> List[Tuple[str, str]]:
        """Return the messages as a list of tuples of role and message."""
        return [(role, message._template) for role, message in self._messages]

    @classmethod
    def restore(
        cls,
        messages: List[Tuple[str, str]],
        template: str,
        template_engine: PromptTemplatingEngine,
        prompt_config: PromptTemplateConfig,
        log: Optional[Logger] = None,
    ) -> "ChatPromptTemplate":
        """Restore a ChatPromptTemplate from a list of tuples of role and message."""
        chat_template = cls(template, template_engine, prompt_config, log)
        for role, message in messages:
            chat_template.add_message(role, message)

        return chat_template
