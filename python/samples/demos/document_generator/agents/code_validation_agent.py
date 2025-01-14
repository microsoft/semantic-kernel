# Copyright (c) Microsoft. All rights reserved.

from samples.demos.document_generator.agents.custom_agent_base import CustomAgentBase
from samples.demos.document_generator.plugins.code_execution_plugin import CodeExecutionPlugin
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior

INSTRUCTION = """
You are a code validation agent in a collaborative document creation chat.

Your task is to validate Python code in the latest document draft and summarize any errors.
Extract and assemble the code snippets into a Python script.
Execute the code to validate it. If there are errors, summarize the error messages.
Do not try to fix the errors.

Stay focused on validating the code.
"""

DESCRIPTION = """
Select me to validate the Python code in the latest document draft.
"""


class CodeValidationAgent(CustomAgentBase):
    def __init__(self):
        kernel = self._create_kernel()
        kernel.add_plugin(plugin=CodeExecutionPlugin(), plugin_name="CodeExecutionPlugin")

        settings = kernel.get_prompt_execution_settings_from_service_id(service_id=CustomAgentBase.AZURE_SERVICE_ID)
        settings.function_choice_behavior = FunctionChoiceBehavior.Auto(maximum_auto_invoke_attempts=1)

        super().__init__(
            kernel=kernel,
            execution_settings=settings,
            name="CodeValidationAgent",
            instructions=INSTRUCTION.strip(),
            description=DESCRIPTION.strip(),
        )
