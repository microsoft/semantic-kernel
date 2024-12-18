# Copyright (c) Microsoft. All rights reserved.

from samples.demos.document_generator.agents.custom_agent_base import CustomAgentBase
from samples.demos.document_generator.plugins.code_execution_plugin import CodeExecutionPlugin
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior

INSTRUCTION = """
Your job is to validate Python code in techincal content and you're great at it!
Read the document and extract the code snippets. Assemble the code snippets into a Python script.
Validate the code snippets for correctness and and make sure the code runs without errors.
If there are errors, don't try to correct them. Return the error messages so that the author can
correct them.
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
            instructions=INSTRUCTION,
            description="Code Validation Agent",
        )
