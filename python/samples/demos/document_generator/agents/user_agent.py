# Copyright (c) Microsoft. All rights reserved.

from samples.demos.document_generator.agents.custom_agent_base import CustomAgentBase
from samples.demos.document_generator.plugins.user_plugin import UserPlugin
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior

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

        settings = kernel.get_prompt_execution_settings_from_service_id(service_id=CustomAgentBase.AZURE_SERVICE_ID)
        settings.function_choice_behavior = FunctionChoiceBehavior.Auto(maximum_auto_invoke_attempts=1)

        super().__init__(
            kernel=kernel,
            execution_settings=settings,
            name="UserAgent",
            instructions=INSTRUCTION.strip(),
            description=DESCRIPTION.strip(),
        )
