# Copyright (c) Microsoft. All rights reserved.

import sys
from collections.abc import AsyncIterable
from typing import TYPE_CHECKING, Any

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from samples.demos.document_generator.agents.custom_agent_base import CustomAgentBase
from samples.demos.document_generator.plugins.user_plugin import UserPlugin
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.functions.kernel_arguments import KernelArguments

if TYPE_CHECKING:
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
        kernel = self._create_kernel()
        kernel.add_plugin(plugin=UserPlugin(), plugin_name="UserPlugin")

        settings = kernel.get_prompt_execution_settings_from_service_id(service_id=CustomAgentBase.SERVICE_ID)
        settings.function_choice_behavior = FunctionChoiceBehavior.Auto(maximum_auto_invoke_attempts=1)

        super().__init__(
            service_id=CustomAgentBase.SERVICE_ID,
            kernel=kernel,
            arguments=KernelArguments(settings=settings),
            name="UserAgent",
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
        cloned_history.add_user_message(
            "Now present the latest draft to the user for feedback and summarize their feedback."
        )

        async for response_message in super().invoke(cloned_history, arguments=arguments, kernel=kernel, **kwargs):
            yield response_message
