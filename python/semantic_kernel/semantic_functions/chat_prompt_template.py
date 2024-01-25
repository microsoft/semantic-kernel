# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
from typing import TYPE_CHECKING, Any, Dict, Generic, List, Optional, TypeVar

from pydantic import Field

from semantic_kernel.models.chat.chat_message import ChatMessage
from semantic_kernel.semantic_functions.prompt_template import PromptTemplate
from semantic_kernel.semantic_functions.prompt_template_config import (
    PromptTemplateConfig,
)
from semantic_kernel.template_engine.protocols.prompt_templating_engine import (
    PromptTemplatingEngine,
)

if TYPE_CHECKING:
    from semantic_kernel.orchestration.kernel_context import KernelContext

ChatMessageT = TypeVar("ChatMessageT", bound=ChatMessage)

logger: logging.Logger = logging.getLogger(__name__)


class ChatPromptTemplate(PromptTemplate, Generic[ChatMessageT]):
    messages: List[ChatMessageT] = Field(default_factory=list)

    def __init__(
        self,
        template: str,
        template_engine: PromptTemplatingEngine,
        prompt_config: PromptTemplateConfig,
        parse_chat_system_prompt: bool = False,
        parse_messages: bool = False,
        **kwargs: Any,
    ) -> None:
        """Initialize a chat prompt template.

        if there is a field 'chat_system_prompt' in the prompt_config.execution_settings.extension_data,
        that value is added to the messages list as a system message,
        can be controlled by setting the parse_chat_system_prompt parameter to True.

        After that any messages that are in messages in the prompt_config.execution_settings
        are added to the messages list.
        Can be controlled by setting the parse_messages parameter to True.

        Arguments:
            template {str} -- The template to use for the chat prompt.
            template_engine {PromptTemplatingEngine} -- The templating engine to use.
            prompt_config {PromptTemplateConfig} -- The prompt config to use.
            parse_chat_system_prompt {bool} -- Whether to parse the chat_system_prompt from
                the prompt_config.execution_settings.extension_data.
            parse_messages {bool} -- Whether to parse the messages from the prompt_config.execution_settings.

        """
        super().__init__(template, template_engine, prompt_config)
        if "log" in kwargs:
            logger.warning("The `log` parameter is deprecated. Please use the `logging` module instead.")

        if parse_chat_system_prompt and "chat_system_prompt" in self.prompt_config.execution_settings.extension_data:
            self.add_system_message(self.prompt_config.execution_settings.extension_data["chat_system_prompt"])

        if (
            parse_messages
            and hasattr(self.prompt_config.execution_settings, "messages")
            and self.prompt_config.execution_settings.messages
        ):
            for message in self.prompt_config.execution_settings.messages:
                self.add_message(**message)

    async def render(self, context: "KernelContext") -> str:
        raise NotImplementedError("Can't call render on a ChatPromptTemplate.\n" "Use render_messages instead.")

    def add_system_message(self, message: str) -> None:
        """Add a system message to the chat template."""
        self.add_message("system", message)

    def add_user_message(self, message: str) -> None:
        """Add a user message to the chat template."""
        self.add_message("user", message)

    def add_assistant_message(self, message: str) -> None:
        """Add an assistant message to the chat template."""
        self.add_message("assistant", message)

    def add_message(self, role: str, message: Optional[str] = None, **kwargs: Any) -> None:
        """Add a message to the chat template.

        Arguments:
            role: The role of the message, one of "user", "assistant", "system".
            message: The message to add, can include templating components.
            kwargs: can be used by inherited classes.
        """
        concrete_message = self.model_fields["messages"].annotation.__args__[0]
        # When the type is not explicitly set, it is still the typevar, replace with generic ChatMessage
        if isinstance(concrete_message, TypeVar):
            concrete_message = ChatMessage
        assert issubclass(concrete_message, ChatMessage)
        if not message and "content" in kwargs:
            message = kwargs["content"]
        self.messages.append(
            concrete_message(
                role=role,
                content_template=PromptTemplate(message, self.template_engine, self.prompt_config) if message else None,
                **kwargs,
            )
        )

    async def render_messages(self, context: "KernelContext") -> List[Dict[str, str]]:
        """Render the content of the message in the chat template, based on the context."""
        if len(self.messages) == 0 or self.messages[-1].role in [
            "assistant",
            "system",
        ]:
            self.add_user_message(message=self.template)
        await asyncio.gather(*[message.render_message(context) for message in self.messages])
        return [message.as_dict() for message in self.messages]

    def dump_messages(self) -> List[Dict[str, str]]:
        """Return the messages as a list of dicts with role, content, name and function_call."""
        return [message.as_dict() for message in self.messages]

    @classmethod
    def restore(
        cls,
        messages: List[Dict[str, str]],
        template: str,
        template_engine: PromptTemplatingEngine,
        prompt_config: PromptTemplateConfig,
        parse_chat_system_prompt: bool = False,
        parse_messages: bool = False,
        **kwargs: Any,
    ) -> "ChatPromptTemplate":
        """Restore a ChatPromptTemplate from a list of role and message pairs.

        The parse_messages and parse_chat_system_prompt parameters control whether
        the messages and chat_system_prompt from the prompt_config.execution_settings
        are parsed and added to the messages list, not whether or not the 'messages'
        from the messages parameter are parsed, those are always parsed.

        Arguments:
            messages {List[Dict[str, str]]} -- The messages to restore,
                the default format is [{"role": "user", "message": "Hi there"}].
                if the ChatPromptTemplate is created with a different message type,
                the messages should contain any fields that are relevant to the message,
                for instance: ChatPromptTemplate[OpenAIChatMessage].restore can be used with a format:
                [{"role": "assistant", "function_call": FunctionCall()}].
            template {str} -- The template to use for the chat prompt.
            template_engine {PromptTemplatingEngine} -- The templating engine to use.
            prompt_config {PromptTemplateConfig} -- The prompt config to use.
            parse_chat_system_prompt {bool} -- Whether to parse the chat_system_prompt from the
                prompt_config.execution_settings.extension_data.
            parse_messages {bool} -- Whether to parse the messages from the prompt_config.execution_settings.

        """
        chat_template = cls(
            template, template_engine, prompt_config, parse_chat_system_prompt, parse_messages, **kwargs
        )
        for message in messages:
            chat_template.add_message(**message)
        return chat_template
