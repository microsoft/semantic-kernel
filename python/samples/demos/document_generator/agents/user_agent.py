# Copyright (c) Microsoft. All rights reserved.

import sys
from collections.abc import AsyncIterable, Awaitable, Callable
from typing import TYPE_CHECKING, Any

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from samples.demos.document_generator.agents.custom_agent_base import CustomAgentBase, Services
from samples.demos.document_generator.plugins.user_plugin import UserPlugin
from semantic_kernel.contents import ChatMessageContent
from semantic_kernel.functions import KernelArguments

if TYPE_CHECKING:
    from semantic_kernel.agents.agent import AgentResponseItem, AgentThread
    from semantic_kernel.kernel import Kernel

INSTRUCTION = """
You are part of a chat with multiple agents working on a document.

Your task is to summarize the user's feedback on the latest draft from the author agent.
Present the draft to the user and summarize their feedback.

Do not try to address the user's feedback in this chat.
"""

DESCRIPTION = """
Select me if you want to ask the user to review the latest draft for publication.
"""


class UserAgent(CustomAgentBase):
    def __init__(self):
        super().__init__(
            service=self._create_ai_service(Services.AZURE_OPENAI),
            plugins=[UserPlugin()],
            name="UserAgent",
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
            additional_user_message="Now present the latest draft to the user for feedback and summarize their feedback.",  # noqa: E501
            **kwargs,
        ):
            yield response
