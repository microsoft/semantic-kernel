# Copyright (c) Microsoft. All rights reserved.

import asyncio
from logging import Logger
from typing import TYPE_CHECKING, Any, Dict, Generic, List, Optional, TypeVar

from semantic_kernel.models.chat.chat_message import ChatMessage
from semantic_kernel.semantic_functions.prompt_template import PromptTemplate
from semantic_kernel.semantic_functions.prompt_template_config import (
    PromptTemplateConfig,
)
from semantic_kernel.template_engine.protocols.prompt_templating_engine import (
    PromptTemplatingEngine,
)

if TYPE_CHECKING:
    from semantic_kernel.orchestration.sk_context import SKContext

ChatMessageT = TypeVar("ChatMessageT", bound=ChatMessage)


class ChatPromptTemplate(PromptTemplate, Generic[ChatMessageT]):
    _messages: List[ChatMessageT]

    def __init__(
        self,
        template: str,
        template_engine: PromptTemplatingEngine,
        prompt_config: PromptTemplateConfig,
        log: Optional[Logger] = None,
    ) -> None:
        super().__init__(template, template_engine, prompt_config, log)
        self._messages = []
        if self._prompt_config.completion.chat_system_prompt:
            self.add_system_message(self._prompt_config.completion.chat_system_prompt)

    async def render_async(self, context: "SKContext") -> str:
        raise NotImplementedError(
            "Can't call render_async on a ChatPromptTemplate.\n"
            "Use render_messages_async instead."
        )

    def add_system_message(self, message: str) -> None:
        """Add a system message to the chat template."""
        self.add_message("system", message)

    def add_user_message(self, message: str) -> None:
        """Add a user message to the chat template."""
        self.add_message("user", message)

    def add_assistant_message(self, message: str) -> None:
        """Add an assistant message to the chat template."""
        self.add_message("assistant", message)

    def add_message(
        self, role: str, message: Optional[str] = None, **kwargs: Any
    ) -> None:
        """Add a message to the chat template.

        Arguments:
            role: The role of the message, one of "user", "assistant", "system".
            message: The message to add, can include templating components.
            kwargs: can be used by inherited classes.
        """
        self._messages.append(
            ChatMessage(
                role=role,
                content_template=PromptTemplate(
                    message, self._template_engine, self._prompt_config
                ),
            )
        )

    async def render_messages_async(self, context: "SKContext") -> List[Dict[str, str]]:
        """Render the content of the message in the chat template, based on the context."""
        if len(self._messages) == 0 or self._messages[-1].role in [
            "assistant",
            "system",
        ]:
            self.add_user_message(message=self._template)
        await asyncio.gather(
            *[message.render_message_async(context) for message in self._messages]
        )
        return [message.as_dict() for message in self._messages]

    @property
    def messages(self) -> List[Dict[str, str]]:
        """Return the messages as a list of dicts with role, content, name."""
        return [message.as_dict() for message in self._messages]

    @classmethod
    def restore(
        cls,
        messages: List[Dict[str, str]],
        template: str,
        template_engine: PromptTemplatingEngine,
        prompt_config: PromptTemplateConfig,
        log: Optional[Logger] = None,
    ) -> "ChatPromptTemplate":
        """Restore a ChatPromptTemplate from a list of role and message pairs.

        If there is a chat_system_prompt in the prompt_config.completion settings,
        that takes precedence over the first message in the list of messages,
        if that is a system message.
        """
        chat_template = cls(template, template_engine, prompt_config, log)
        if (
            prompt_config.completion.chat_system_prompt
            and messages[0]["role"] == "system"
        ):
            existing_system_message = messages.pop(0)
            if (
                existing_system_message["message"]
                != prompt_config.completion.chat_system_prompt
            ):
                chat_template._log.info(
                    "Overriding system prompt with chat_system_prompt, old system message: %s, new system message: %s",
                    existing_system_message["message"],
                    prompt_config.completion.chat_system_prompt,
                )
        for message in messages:
            chat_template.add_message(message["role"], message["message"])

        return chat_template
