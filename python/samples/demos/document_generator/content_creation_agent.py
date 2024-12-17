# Copyright (c) Microsoft. All rights reserved.

from samples.demos.document_generator.agent_base_extension import AgentBaseExtension
from samples.demos.document_generator.repo_file_plugin import RepoFilePlugin
from semantic_kernel.agents.chat_completion.chat_completion_agent import ChatCompletionAgent
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior

INSTRUCTION = """
Your job is to create technical content to share knowledge and you're great at it!
The contents you create are always informative and engaging.
You also write code snippets to help explain concepts or demonstrate how to use a feature.
"""


class ContentCreationAgent(ChatCompletionAgent, AgentBaseExtension):
    def __init__(self):
        kernel = self._create_kernel()
        kernel.add_plugin(plugin=RepoFilePlugin(), plugin_name="RepoFilePlugin")

        settings = kernel.get_prompt_execution_settings_from_service_id(
            service_id=AgentBaseExtension.AZURE_AI_INFERENCE_SERVICE_ID
        )
        settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

        super().__init__(
            kernel=kernel,
            execution_settings=settings,
            name="ContentCreationAgent",
            instructions=INSTRUCTION,
            description="Content Creation Agent",
        )
