# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from semantic_kernel.semantic_functions.prompt_template import PromptTemplate
from semantic_kernel.semantic_functions.prompt_template_config import (
    PromptTemplateConfig,
)
from semantic_kernel.sk_pydantic import SKBaseModel
from semantic_kernel.template_engine.protocols.prompt_templating_engine import (
    PromptTemplatingEngine,
)

if TYPE_CHECKING:
    from semantic_kernel.orchestration.sk_context import SKContext


class ChatMessage(SKBaseModel):
    role: str
    name: Optional[str] = None
    content: Optional[str] = None
    message: Optional[str] = None


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
            self.add_system_message(self._prompt_config.completion.chat_system_prompt)

    async def render_async(self, context: "SKContext") -> str:
        raise NotImplementedError(
            "Can't call render_async on a ChatPromptTemplate.\n"
            "Use render_messages_async instead."
        )

    def add_system_message(self, message: str) -> None:
        self.add_message(ChatMessage(role="system", message=message))

    def add_user_message(self, message: str) -> None:
        self.add_message(
            ChatMessage(
                role="user",
                message=message,
            )
        )

    def add_function_response_message(self, name: str, content: Any) -> None:
        self.add_message(ChatMessage(role="function", name=name, content=str(content)))

    def add_assistant_message(
        self,
        message: Optional[str] = None,
        function_call: Optional[Dict[str, str]] = None,
    ) -> None:
        name = None
        content = None
        if function_call:
            name = function_call.get("name")
            content = str(function_call.get("arguments"))
        self.add_message(
            ChatMessage(role="assistant", name=name, message=message, content=content)
        )

    def add_message(
        self,
        message: ChatMessage,
    ) -> None:
        self._messages.append(message)

    async def render_messages_async(self, context: "SKContext") -> List[Dict[str, str]]:
        rendered_messages: List[Dict[str, str]] = []
        for mess in self._messages:
            new_message = {"role": mess.role}
            if mess.message:
                new_message["content"] = await PromptTemplate(
                    mess.message, self._template_engine, self._prompt_config
                ).render_async(context)
            if mess.name:
                new_message["name"] = mess.name
            if mess.content:
                if "content" in new_message:
                    new_message["content"] += f" {mess.content}"
                else:
                    new_message["content"] = mess.content
            rendered_messages.append(new_message)

        latest_user_message = await self._template_engine.render_async(
            self._template, context
        )
        rendered_messages.append({"role": "user", "content": latest_user_message})

        return rendered_messages

    @property
    def messages(self) -> List[Dict[str, str]]:
        """Return the messages as a list of tuples of role and message."""
        return [
            {"role": role, "message": message._template}
            for role, message in self._messages
        ]

    @classmethod
    def restore(
        cls,
        messages: List[Dict[str, str]],
        template: str,
        template_engine: PromptTemplatingEngine,
        prompt_config: PromptTemplateConfig,
        log: Optional[Logger] = None,
    ) -> "ChatPromptTemplate":
        """Restore a ChatPromptTemplate from a list of role and message pairs."""
        chat_template = cls(template, template_engine, prompt_config, log)

        if prompt_config.chat_system_prompt:
            chat_template.add_system_message(
                prompt_config.completion.chat_system_prompt
            )

        for message in messages:
            chat_template.add_message(message["role"], message["message"])

        return chat_template
