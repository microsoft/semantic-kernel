# Copyright (c) Microsoft. All rights reserved.

from samples.demos.document_generator.agents.custom_agent_base import CustomAgentBase
from samples.demos.document_generator.plugins.repo_file_plugin import RepoFilePlugin
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior

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

        settings = kernel.get_prompt_execution_settings_from_service_id(service_id=CustomAgentBase.AZURE_SERVICE_ID)
        settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

        super().__init__(
            kernel=kernel,
            execution_settings=settings,
            name="ContentCreationAgent",
            instructions=INSTRUCTION.strip(),
            description=DESCRIPTION.strip(),
        )
