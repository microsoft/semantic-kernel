# Copyright (c) Microsoft. All rights reserved.

from samples.demos.document_generator.agents.custom_agent_base import CustomAgentBase
from samples.demos.document_generator.plugins.code_execution_plugin import CodeExecutionPlugin
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior

INSTRUCTION = """
You are a code validation agent in a collaborative document creation chat.

Your task is to validate Python code in the latest document draft.
Extract and assemble the code snippets into a Python script.
Check the code for errors and ensure it runs correctly.
If there are errors, return the error messages for correction.

Stay focused on validating the code.
"""

DESCRIPTION = """
I am a code validation agent. My job is to check Python code in documents for correctness.
Call me when you need to validate code snippets in a document.
If the code is correct, I will return the output.
If there are errors, I will return the error messages for correction.
"""


class CodeValidationAgent(CustomAgentBase):
    def __init__(self):
        kernel = self._create_kernel()
        kernel.add_plugin(plugin=CodeExecutionPlugin(), plugin_name="CodeExecutionPlugin")

        settings = kernel.get_prompt_execution_settings_from_service_id(service_id=CustomAgentBase.AZURE_SERVICE_ID)
        settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

        super().__init__(
            kernel=kernel,
            execution_settings=settings,
            name="CodeValidationAgent",
            instructions=INSTRUCTION.strip(),
            description=DESCRIPTION.strip(),
        )
