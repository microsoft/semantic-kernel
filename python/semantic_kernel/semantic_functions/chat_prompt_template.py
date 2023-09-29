# Copyright (c) Microsoft. All rights reserved.

import asyncio
from logging import Logger
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from semantic_kernel.connectors.ai.open_ai.models.chat.chat_message import ChatMessage
from semantic_kernel.connectors.ai.open_ai.models.chat.function_call import FunctionCall
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
    _messages: List[ChatMessage]

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
            self._messages.append(
                ChatMessage(
                    role="system",
                    fixed_content=self._prompt_config.completion.chat_system_prompt,
                )
            )

    async def render_async(self, context: "SKContext") -> str:
        raise NotImplementedError(
            "Can't call render_async on a ChatPromptTemplate.\n"
            "Use render_messages_async instead."
        )

    def add_system_message(self, message: str, name: Optional[str] = None) -> None:
        """Add a system message to the chat template."""
        self.add_message("system", message, name)

    def add_user_message(self, message: str, name: Optional[str] = None) -> None:
        """Add a user message to the chat template."""
        self.add_message("user", message, name)

    def add_function_response_message(self, name: str, content: Any) -> None:
        """Add a function response message to the chat template."""
        self._messages.append(
            ChatMessage(role="function", name=name, fixed_content=str(content))
        )

    def add_assistant_message(
        self,
        message: Optional[str] = None,
        function_call: Optional["FunctionCall"] = None,
    ) -> None:
        """Add an assistant message to the chat template."""
        self._messages.append(
            ChatMessage(
                role="assistant",
                content_template=PromptTemplate(
                    message, self._template_engine, self._prompt_config
                ),
                function_call=function_call,
            )
        )

    def add_message(self, role: str, message: str, name: Optional[str] = None) -> None:
        """Add a message to the chat template."""
        self._messages.append(
            ChatMessage(
                role=role,
                content_template=PromptTemplate(
                    message, self._template_engine, self._prompt_config
                ),
                name=name,
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
        """Restore a ChatPromptTemplate.

        Args:
            messages (List[Dict[str, str]]): List of dicts with 'role', 'content', and optionally 'name'.
            template (str): Template string.
            template_engine (PromptTemplatingEngine): Template engine.
            prompt_config (PromptTemplateConfig): Prompt config.
            log (Optional[Logger], optional): Logger. Defaults to None.

        Returns:
            ChatPromptTemplate: ChatPromptTemplate restored from messages.
        """
        chat_template = cls(template, template_engine, prompt_config, log)

        if prompt_config.chat_system_prompt:
            chat_template.add_system_message(
                prompt_config.completion.chat_system_prompt
            )

        for message in messages:
            chat_template._messages.append(
                ChatMessage(
                    role=message["role"],
                    fixed_content=message["content"],
                    name=message.get("name"),
                )
            )

        return chat_template
