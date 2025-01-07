# Copyright (c) Microsoft. All rights reserved.

from samples.demos.document_generator.agents.custom_agent_base import CustomAgentBase
from samples.demos.document_generator.plugins.code_execution_plugin import CodeExecutionPlugin
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior

INSTRUCTION = """
You will be given a chat history where multiple agents (including yourself) are involved in creating a document.

Your job is to validate Python code in techincal content and you're great at it!
Read the document and extract the code snippets. Assemble the code snippets into a Python script.
Validate the code snippets for correctness and and make sure the code runs without errors.
If there are errors, don't try to correct them. Return the error messages so that the author can
correct them.
"""

DESCRIPTION = """
I am a code validation agent whose job is to validate Python code in technical content.
Invoke me when there are code snippets in the document that need to be validated.
"""


class CodeValidationAgent(CustomAgentBase):
    def __init__(self):
        kernel = self._create_kernel()
        kernel.add_plugin(plugin=CodeExecutionPlugin(), plugin_name="CodeExecutionPlugin")

        settings = kernel.get_prompt_execution_settings_from_service_id(
            service_id=CustomAgentBase.AZURE_AI_INFERENCE_SERVICE_ID
        )
        settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

        super().__init__(
            kernel=kernel,
            execution_settings=settings,
            name="CodeValidationAgent",
            instructions=INSTRUCTION.strip(),
            description=DESCRIPTION.strip(),
        )
