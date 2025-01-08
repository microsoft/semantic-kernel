# Copyright (c) Microsoft. All rights reserved.

from samples.demos.document_generator.agents.custom_agent_base import CustomAgentBase
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior

INSTRUCTION = """
You will be given a chat history where multiple agents (including yourself) are involved in creating a document.

Your job is to read the latest draft and provide feedback on the content to the author.
You provide feedback on the following:
- The completeness of the content: Will the reader get a full understanding of the topic?
- The accuracy of the content: Is the information correct?
- The clarity of the content: Is the content easy to understand?
- The engagement of the content: Is the content engaging?
- The coherence of the content: Does the content flow well?

At the end, try to list some questions you think the reader might have after reading the content
so that the author can address them in the next revision.

If you think the content is ready for publication, let the author know.
"""

DESCRIPTION = """
I am a proofread agent whose job is to provide feedback on technical content.
Invoke me to provide feedback on the content to the author whenever the content is ready for review.
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
