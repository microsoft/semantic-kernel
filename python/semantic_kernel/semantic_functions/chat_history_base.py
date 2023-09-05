# Base class for reading and write chat history
from abc import abstractmethod
from dataclasses import asdict
from logging import Logger
from typing import TYPE_CHECKING, Any, Dict, List, Optional

if TYPE_CHECKING:
    from semantic_kernel import Kernel

from semantic_kernel.semantic_functions.chat_prompt_template import ChatPromptTemplate
from semantic_kernel.semantic_functions.prompt_template_config import (
    PromptTemplateConfig,
)
from semantic_kernel.template_engine.protocols.prompt_templating_engine import (
    PromptTemplatingEngine,
)


class ChatHistoryBase:
    def __init__(
        self,
        template: str,
        template_engine: PromptTemplatingEngine,
        prompt_config: PromptTemplateConfig,
        messages: Optional[List[Dict[str, str]]] = None,
        log: Optional[Logger] = None,
    ) -> None:
        """Create a new ChatHistoryBase instance.

        Args:
            template (str): The template to use for rendering the chat history.
            template_engine (PromptTemplatingEngine): The template engine to use for rendering the chat history.
            prompt_config (PromptTemplateConfig): The prompt config to use for rendering the chat history.
            messages (Optional[List[Dict[str, str]]], optional): The chat history to load. Defaults to None.
            log (Optional[Logger], optional): The logger to use. Defaults to None.
        """
        self._template = template
        self._template_engine = template_engine
        self._prompt_config = prompt_config
        self._log = log

        if messages:
            self._chat_prompt_template = ChatPromptTemplate.restore(
                messages,
                template=self._template,
                template_engine=self._template_engine,
                prompt_config=self._prompt_config,
                log=self._log,
            )
        else:
            self._chat_prompt_template = ChatPromptTemplate(
                self._template, self._template_engine, self._prompt_config, self._log
            )

    @property
    def chat_prompt_template(self) -> ChatPromptTemplate:
        """Get the chat prompt template."""
        return self._chat_prompt_template

    @property
    def prompt_config(self) -> PromptTemplateConfig:
        """Get the prompt config."""
        return self._prompt_config

    @abstractmethod
    async def load_async(self, messages_only: bool = False) -> None:
        """Load chat history from storage.

        Args:
            messages_only (bool, optional): Whether to only load the messages.
                When true, the template and prompt config are not loaded.
                Defaults to False.
        """
        pass

    @abstractmethod
    async def save_async(self, messages_only: bool = False) -> None:
        """Save chat history to storage.

        Args:
            messages_only (bool, optional): Whether to only save the messages.
                When true, the template and prompt config are not loaded.
                Defaults to False.
        """
        pass

    def _get_saveable_object(self, messages_only: bool = False) -> Dict[str, Any]:
        if messages_only:
            return self._get_messages()
        else:
            return {
                "template": self._template,
                "prompt_config": asdict(self._prompt_config),
                "messages": self._get_messages(),
            }

    def _parse_loaded_object(
        self, loaded_object: Dict[str, Any], messages_only: bool = False
    ) -> None:
        if messages_only:
            self._load_messages(loaded_object)
            return

        if "template" not in loaded_object:
            raise ValueError("template not found in loaded object")
        if "prompt_config" not in loaded_object:
            raise ValueError("prompt_config not found in loaded object")
        if "messages" not in loaded_object:
            raise ValueError("messages not found in loaded object")
        self._template = loaded_object["template"]
        self._prompt_config = PromptTemplateConfig.from_dict(
            loaded_object["prompt_config"]
        )
        self._load_messages(loaded_object["messages"])

    def _load_messages(self, messages) -> None:
        """Load messages into the chat prompt template, overwriting any existing messages."""
        self._chat_prompt_template = ChatPromptTemplate.restore(
            messages,
            self._template,
            self._template_engine,
            self._prompt_config,
            self._log,
        )

    def _get_messages(self) -> List[Dict[str, str]]:
        if self._chat_prompt_template is None:
            return []
        return self._chat_prompt_template.messages

    @classmethod
    @abstractmethod
    async def load_async_from_store(
        cls, kernel: "Kernel", **kwargs
    ) -> "ChatHistoryBase":
        """Create a new FileChatHistory instance from a file.

        Args:
            kernel (Kernel): The kernel to use, for the prompt template engine.
            **kwargs: Any additional arguments.

        Returns:
            ChatHistoryBase (or a subclass thereof): The loaded chat history.
        """
