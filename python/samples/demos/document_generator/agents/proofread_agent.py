# Copyright (c) Microsoft. All rights reserved.

from samples.demos.document_generator.agents.custom_agent_base import CustomAgentBase
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior

INSTRUCTION = """
You are part of a chat with multiple agents working on a document.

Your task is to review the latest draft and provide feedback on:
- Completeness: Does it cover the topic fully?
- Accuracy: Is the information correct?
- Clarity: Is it easy to understand?
- Engagement: Is it interesting?
- Coherence: Does it flow well?

List any questions a reader might have after reading to help the author improve the next revision.

If the content is ready for publication, inform the author.

Stay focused on your task.
"""

DESCRIPTION = """
Select me if you want to someone to proofread the latest draft and provide feedback.
"""


class ProofreadAgent(CustomAgentBase):
    def __init__(self):
        kernel = self._create_kernel()

        settings = kernel.get_prompt_execution_settings_from_service_id(service_id=CustomAgentBase.AZURE_SERVICE_ID)
        settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

        super().__init__(
            kernel=kernel,
            execution_settings=settings,
            name="ProofreadAgent",
            instructions=INSTRUCTION.strip(),
            description=DESCRIPTION.strip(),
        )
