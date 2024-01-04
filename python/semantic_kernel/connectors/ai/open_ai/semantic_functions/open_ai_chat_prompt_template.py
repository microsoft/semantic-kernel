# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import Any, Dict, List, Optional

from semantic_kernel.connectors.ai.open_ai.models.chat.open_ai_chat_message import (
    OpenAIChatMessage,
)
from semantic_kernel.semantic_functions.chat_prompt_template import ChatPromptTemplate
from semantic_kernel.semantic_functions.prompt_template import PromptTemplate
from semantic_kernel.semantic_functions.prompt_template_config import (
    PromptTemplateConfig,
)
from semantic_kernel.template_engine.protocols.prompt_templating_engine import (
    PromptTemplatingEngine,
)

logger: logging.Logger = logging.getLogger(__name__)


class OpenAIChatPromptTemplate(ChatPromptTemplate[OpenAIChatMessage]):
    def add_function_response_message(self, name: str, content: Any) -> None:
        """Add a function response message to the chat template."""
        self.messages.append(OpenAIChatMessage(role="function", name=name, fixed_content=str(content)))

    def add_message(self, role: str, message: Optional[str] = None, **kwargs: Any) -> None:
        """Add a message to the chat template.

        Arguments:
            role: The role of the message, one of "user", "assistant", "system", "function"
            message: The message to add, can include templating components.
            kwargs: can be used by inherited classes.
                name: the name of the function that was used, to be used with role: function
                function_call: the function call that is specified, to be used with role: assistant
        """
        name = kwargs.get("name")
        if name is not None and role != "function":
            logger.warning("name is only used with role: function, ignoring")
            name = None
        function_call = kwargs.get("function_call")
        if function_call is not None:
            if role == "assistant":
                self.messages.append(
                    OpenAIChatMessage(
                        role=role,
                        fixed_content=message,
                        name=name,
                        function_call=function_call,
                    )
                )
                return
            self._log.warning("function_call is only used with role: assistant, ignoring")
            function_call = None
        self.messages.append(
            OpenAIChatMessage(
                role=role,
                content_template=PromptTemplate(message, self.template_engine, self.prompt_config),
                name=name,
                function_call=function_call,
            )
        )

    @classmethod
    def restore(
        cls,
        messages: List[Dict[str, str]],
        template: str,
        template_engine: PromptTemplatingEngine,
        prompt_config: PromptTemplateConfig,
        log: Optional[Any] = None,
    ) -> "OpenAIChatPromptTemplate":
        """Restore a ChatPromptTemplate from a list of role and message pairs.

        If there is a chat_system_prompt in the prompt_config.completion settings,
        that takes precedence over the first message in the list of messages,
        if that is a system message.
        """
        if log:
            logger.warning("The `log` parameter is deprecated. Please use the `logging` module instead.")
        chat_template = cls(template, template_engine, prompt_config)
        if prompt_config.completion.chat_system_prompt and messages[0]["role"] == "system":
            existing_system_message = messages.pop(0)
            if existing_system_message["message"] != prompt_config.completion.chat_system_prompt:
                logger.info(
                    "Overriding system prompt with chat_system_prompt, old system message: %s, new system message: %s",
                    existing_system_message["message"],
                    prompt_config.completion.chat_system_prompt,
                )
        for message in messages:
            chat_template.add_message(
                message["role"],
                message["message"],
                name=message["name"],
                function_call=message["function_call"],
            )

        return chat_template
