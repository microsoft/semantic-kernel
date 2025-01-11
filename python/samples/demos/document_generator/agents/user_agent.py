# Copyright (c) Microsoft. All rights reserved.

from samples.demos.document_generator.agents.custom_agent_base import CustomAgentBase
from samples.demos.document_generator.plugins.user_plugin import UserPlugin
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior

INSTRUCTION = """
You are in a chat where multiple agents (including yourself) are involved in creating a document.

The document may be been through multiple revisions.

Your job is to ask the user for feedback and suggestions.
Please find the latest draft written by the author agent for the chat and present it to the user for feedback.
Note that you will have to interact with the user via functions.
Once the user has responded, do NOT try to address the feedback or make changes to the document.

Simply summarize the response and return it to the author.

Focus on your task and do not get distracted by other agents.
"""

DESCRIPTION = """
I am a user agent whose job is to request feedback from users.
I can present the latest draft of the document to the user for feedback and suggestions.
Invoke me when the document is verified, ready for publication and it needs final feedback.
I will return the user's feedback when they respond.
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
