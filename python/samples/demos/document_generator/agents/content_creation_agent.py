# Copyright (c) Microsoft. All rights reserved.

import sys
from collections.abc import AsyncIterable, Awaitable, Callable
from typing import TYPE_CHECKING, Any

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from samples.demos.document_generator.agents.custom_agent_base import CustomAgentBase, Services
from samples.demos.document_generator.plugins.repo_file_plugin import RepoFilePlugin
from semantic_kernel.contents import ChatMessageContent
from semantic_kernel.functions import KernelArguments

if TYPE_CHECKING:
    from semantic_kernel.agents import AgentResponseItem, AgentThread
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
        super().__init__(
            service=self._create_ai_service(Services.AZURE_OPENAI),
            plugins=[RepoFilePlugin()],
            name="ContentCreationAgent",
            instructions=INSTRUCTION.strip(),
            description=DESCRIPTION.strip(),
        )

    @override
    async def invoke(
        self,
        *,
        messages: str | ChatMessageContent | list[str | ChatMessageContent] | None = None,
        thread: "AgentThread | None" = None,
        on_intermediate_message: Callable[[ChatMessageContent], Awaitable[None]] | None = None,
        arguments: KernelArguments | None = None,
        kernel: "Kernel | None" = None,
        **kwargs: Any,
    ) -> AsyncIterable["AgentResponseItem[ChatMessageContent]"]:
        async for response in super().invoke(
            messages=messages,
            thread=thread,
            on_intermediate_message=on_intermediate_message,
            arguments=arguments,
            kernel=kernel,
            additional_user_message="Now generate new content or revise existing content to incorporate feedback.",
            **kwargs,
        ):
            yield response
