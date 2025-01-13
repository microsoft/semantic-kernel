# Copyright (c) Microsoft. All rights reserved.

from samples.demos.document_generator.agents.custom_agent_base import CustomAgentBase
from samples.demos.document_generator.plugins.user_plugin import UserPlugin
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior

INSTRUCTION = """
You are part of a chat with multiple agents working on a document.

Your task is to ask the user for feedback on the latest draft from the author agent.
Present the draft to the user and collect their feedback.

Do not attempt to address the user's feedback.
Summarize the user's feedback and return it to the author agent.

Stay focused on your task.
"""

DESCRIPTION = """
I am a user agent responsible for gathering user feedback on document drafts.
I present the latest draft to the user and collect their suggestions.
Invoke me when the document is ready for final feedback before publication.
I will return the user's feedback promptly.
"""


class UserAgent(CustomAgentBase):
    def __init__(self):
        kernel = self._create_kernel()
        kernel.add_plugin(plugin=UserPlugin(), plugin_name="UserPlugin")

        settings = kernel.get_prompt_execution_settings_from_service_id(service_id=CustomAgentBase.AZURE_SERVICE_ID)
        settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

        super().__init__(
            kernel=kernel,
            execution_settings=settings,
            name="UserAgent",
            instructions=INSTRUCTION.strip(),
            description=DESCRIPTION.strip(),
        )
