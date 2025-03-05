# Copyright (c) Microsoft. All rights reserved.

import sys
from collections.abc import AsyncIterable
from typing import TYPE_CHECKING, Any

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

from samples.demos.document_generator.agents.custom_agent_base import CustomAgentBase
from samples.demos.document_generator.plugins.code_execution_plugin import CodeExecutionPlugin
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.functions.kernel_arguments import KernelArguments

if TYPE_CHECKING:
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
        kernel = self._create_kernel()
        kernel.add_plugin(plugin=CodeExecutionPlugin(), plugin_name="CodeExecutionPlugin")

        settings = kernel.get_prompt_execution_settings_from_service_id(service_id=CustomAgentBase.SERVICE_ID)
        settings.function_choice_behavior = FunctionChoiceBehavior.Auto(maximum_auto_invoke_attempts=1)

        super().__init__(
            service_id=CustomAgentBase.SERVICE_ID,
            kernel=kernel,
            arguments=KernelArguments(settings=settings),
            name="CodeValidationAgent",
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
            "Now validate the Python code in the latest document draft and summarize any errors."
        )

        async for response_message in super().invoke(cloned_history, arguments=arguments, kernel=kernel, **kwargs):
            yield response_message
