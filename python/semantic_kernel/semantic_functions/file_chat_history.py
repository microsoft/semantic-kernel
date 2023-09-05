import json
from logging import Logger
from typing import Dict, List

from semantic_kernel.kernel import Kernel
from semantic_kernel.semantic_functions.chat_history_base import ChatHistoryBase
from semantic_kernel.semantic_functions.prompt_template_config import (
    PromptTemplateConfig,
)
from semantic_kernel.template_engine.protocols.prompt_templating_engine import (
    PromptTemplatingEngine,
)


class FileChatHistory(ChatHistoryBase):
    def __init__(
        self,
        path: str,
        template: str,
        template_engine: PromptTemplatingEngine,
        prompt_config: PromptTemplateConfig,
        messages: List[Dict[str, str]] | None = None,
        log: Logger | None = None,
    ) -> None:
        super().__init__(template, template_engine, prompt_config, messages, log)
        self._path = path

    async def load_async(self, messages_only: bool = False) -> None:
        """Load chat history from a file."""
        with open(self._path, "r") as f:
            self._parse_loaded_object(json.load(f), messages_only)

    async def save_async(self, messages_only: bool = False) -> None:
        """Save chat history to a file."""
        with open(self._path, "w") as f:
            json.dump(self._get_saveable_object(messages_only), f, indent=2)

    @classmethod
    async def load_async_from_store(
        cls,
        kernel: "Kernel",
        path: str,
    ) -> "FileChatHistory":
        """Create a new FileChatHistory instance from a file.

        Args:
            kernel (Kernel): The kernel to use, for the prompt template engine.
            path (str): The path to the file to load.

        Returns:
            FileChatHistory: The loaded chat history.
        """
        chat_history = FileChatHistory(
            path, "", kernel.prompt_template_engine, PromptTemplateConfig()
        )
        await chat_history.load_async(messages_only=False)
        return chat_history
