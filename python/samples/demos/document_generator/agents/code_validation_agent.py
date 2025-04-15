# Copyright (c) Microsoft. All rights reserved.

import sys
from collections.abc import AsyncIterable, Awaitable, Callable
from typing import TYPE_CHECKING, Any

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from samples.demos.document_generator.agents.custom_agent_base import CustomAgentBase, Services
from samples.demos.document_generator.plugins.code_execution_plugin import CodeExecutionPlugin
from semantic_kernel.contents import ChatMessageContent
from semantic_kernel.functions import KernelArguments

if TYPE_CHECKING:
    from semantic_kernel.agents.agent import AgentResponseItem, AgentThread
    from semantic_kernel.kernel import Kernel

INSTRUCTION = """
You are a code validation agent in a collaborative document creation chat.

Your task is to validate Python code in the latest document draft and summarize any errors.
Follow the instructions in the document to assemble the code snippets into a single Python script.
If the snippets in the document are from multiple scripts, you need to modify them to work together as a single script.
Execute the code to validate it. If there are errors, summarize the error messages.

Do not try to fix the errors.
"""

DESCRIPTION = """
Select me to validate the Python code in the latest document draft.
"""


class CodeValidationAgent(CustomAgentBase):
    def __init__(self):
        super().__init__(
            service=self._create_ai_service(Services.AZURE_OPENAI),
            plugins=[CodeExecutionPlugin()],
            name="CodeValidationAgent",
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
            additional_user_message="Now validate the Python code in the latest document draft and summarize any errors.",  # noqa: E501
            **kwargs,
        ):
            yield response
