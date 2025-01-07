# Copyright (c) Microsoft. All rights reserved.

from samples.demos.document_generator.agents.custom_agent_base import CustomAgentBase
from samples.demos.document_generator.plugins.user_input_plugin import UserInputPlugin
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior

INSTRUCTION = """
You will be given a chat history where multiple agents (including yourself) are involved in creating a document.

Your job is to present the latest draft of the document to the user for feedback and suggestions.
Once the user has responded, summarize the response and return it to the author.

DO NOT attemp to provide your own feedback or suggestions.
DO NOT attemp to provide any corrections or modifications to the content.
"""

DESCRIPTION = """
I am a user agent whose job is to request feedback from users.
I can present the latest draft of the document to the user for feedback and suggestions.
Invoke me when the document is almost ready for publication and you need final feedback.
"""


class UserAgent(CustomAgentBase):
    def __init__(self):
        kernel = self._create_kernel()
        kernel.add_plugin(plugin=UserInputPlugin(), plugin_name="UserInputPlugin")

        settings = kernel.get_prompt_execution_settings_from_service_id(
            service_id=CustomAgentBase.AZURE_AI_INFERENCE_SERVICE_ID
        )
        settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

        super().__init__(
            kernel=kernel,
            execution_settings=settings,
            name="UserAgent",
            instructions=INSTRUCTION.strip(),
            description=DESCRIPTION.strip(),
        )
