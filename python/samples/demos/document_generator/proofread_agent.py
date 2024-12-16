# Copyright (c) Microsoft. All rights reserved.

from samples.demos.document_generator.agent_base_extension import AgentBaseExtension
from semantic_kernel.agents.chat_completion.chat_completion_agent import ChatCompletionAgent
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior

INSTRUCTION = """
Your job is to read technical content and provide feedback on the content to the author.
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


class ProofreadAgent(ChatCompletionAgent, AgentBaseExtension):
    def __init__(self):
        kernel = self._create_kernel()

        settings = kernel.get_prompt_execution_settings_from_service_id(
            service_id=AgentBaseExtension.AZURE_AI_INFERENCE_SERVICE_ID
        )
        settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

        super().__init__(
            kernel=kernel,
            execution_settings=settings,
            instructions=INSTRUCTION,
            description="QA Agent",
        )
