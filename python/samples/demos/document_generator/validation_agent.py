# Copyright (c) Microsoft. All rights reserved.

from samples.demos.document_generator.agent_base_extension import AgentBaseExtension
from semantic_kernel.agents.chat_completion.chat_completion_agent import ChatCompletionAgent

INSTRUCTION = """
Your job is to validate the code snippets in technical content.
Follow the instructions in the content and run the code snippets to ensure they work as expected.
"""


class ValidationAgent(ChatCompletionAgent, AgentBaseExtension):
    def __init__(self):
        kernel = self._create_kernel()

        settings = kernel.get_prompt_execution_settings_from_service_id(
            service_id=AgentBaseExtension.AZURE_AI_INFERENCE_SERVICE_ID
        )

        super().__init__(
            kernel=kernel,
            execution_settings=settings,
            instructions=INSTRUCTION,
            description="Validation Agent",
        )
