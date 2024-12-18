# Copyright (c) Microsoft. All rights reserved.

from samples.demos.document_generator.agents.custom_agent_base import CustomAgentBase
from samples.demos.document_generator.plugins.repo_file_plugin import RepoFilePlugin
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior

INSTRUCTION = """
Your job is to create technical content to share knowledge and you're great at it!
The contents you create are always informative and engaging.
You also write code snippets to help explain concepts or demonstrate how to use a feature.
"""


class ContentCreationAgent(CustomAgentBase):
    def __init__(self):
        kernel = self._create_kernel()
        kernel.add_plugin(plugin=RepoFilePlugin(), plugin_name="RepoFilePlugin")

        settings = kernel.get_prompt_execution_settings_from_service_id(
            service_id=CustomAgentBase.AZURE_AI_INFERENCE_SERVICE_ID
        )
        settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

        super().__init__(
            kernel=kernel,
            execution_settings=settings,
            name="ContentCreationAgent",
            instructions=INSTRUCTION,
            description="Content Creation Agent",
        )
