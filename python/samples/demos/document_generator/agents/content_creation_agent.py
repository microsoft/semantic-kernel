# Copyright (c) Microsoft. All rights reserved.

import sys
from collections.abc import AsyncIterable
from typing import TYPE_CHECKING, Any

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from samples.demos.document_generator.agents.custom_agent_base import CustomAgentBase
from samples.demos.document_generator.plugins.repo_file_plugin import RepoFilePlugin
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.functions.kernel_arguments import KernelArguments

if TYPE_CHECKING:
    from semantic_kernel.kernel import Kernel

INSTRUCTION = """
You are part of a chat with multiple agents focused on creating technical content.

Your task is to generate informative and engaging technical content,
including code snippets to explain concepts or demonstrate features.
Incorporate feedback by providing the updated full content with changes.
"""

DESCRIPTION = """
Select me to generate new content or to revise existing content.
"""


class ContentCreationAgent(CustomAgentBase):
    def __init__(self):
        kernel = self._create_kernel()
        kernel.add_plugin(plugin=RepoFilePlugin(), plugin_name="RepoFilePlugin")

        settings = kernel.get_prompt_execution_settings_from_service_id(service_id=CustomAgentBase.SERVICE_ID)
        settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

        super().__init__(
            service_id=CustomAgentBase.SERVICE_ID,
            kernel=kernel,
            arguments=KernelArguments(settings=settings),
            name="ContentCreationAgent",
            instructions=INSTRUCTION.strip(),
            description=DESCRIPTION.strip(),
        )

    @override
    async def invoke(
        self,
        history: ChatHistory,
        arguments: KernelArguments | None = None,
        kernel: "Kernel | None" = None,
        **kwargs: Any,
    ) -> AsyncIterable[ChatMessageContent]:
        cloned_history = history.model_copy(deep=True)
        cloned_history.add_user_message("Now generate new content or revise existing content to incorporate feedback.")

        async for response_message in super().invoke(cloned_history, arguments=arguments, kernel=kernel, **kwargs):
            yield response_message
