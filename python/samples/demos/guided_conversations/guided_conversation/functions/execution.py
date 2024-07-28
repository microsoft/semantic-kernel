# Copyright (c) Microsoft. All rights reserved.

from typing import Annotated

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.functions import FunctionResult, KernelArguments
from semantic_kernel.functions.kernel_function_decorator import kernel_function

execution_template = """<message role="system">You are a helpful, thoughtful, and meticulous assistant. 
You are conducting a conversation with a user. Your goal is to complete an artifact as thoroughly as possible by the end of the conversation.
You will be given some reasoning about the best possible action(s) to take next given the state of the conversation as well as the artifact schema.
The reasoning is supposed to state the recommended action(s) to take next, along with all required parameters for each action.
Your task is to execute ALL actions recommended in the reasoning in the order they are listed.
If the reasoning's specification of an action is incomplete (e.g. it doesn't include all required parameters for the action, \
or some parameters are specified implicitly, such as "send a message that contains a greeting" instead of explicitly providing \
the value of the "message" parameter), do not execute the action. You should never fill in missing or imprecise parameters yourself.
If the reasoning is not clear about which actions to take, or all actions are specified in an incomplete way, \
return 'None' without selecting any action.</message>

<message role="user">Artifact schema:
{{ artifact_schema }}

If the type in the schema is str, the "field_value" parameter in the action should be also be a string.
These are example parameters for the update_artifact action: {"field_name": "company_name", "field_value": "Contoso"}
DO NOT write JSON in the "field_value" parameter in this case. {"field_name": "company_name", "field_value": "{"value": "Contoso"}"} is INCORRECT.

Reasoning:
{{ reasoning }}</message>"""


@kernel_function(name="send_message_to_user", description="Sends a message to the user.")
def send_message(message: Annotated[str, "The message to send to the user."]) -> None:
    return None


@kernel_function(name="end_conversation", description="Ends the conversation.")
def end_conversation() -> None:
    return None


async def execution(
    kernel: Kernel, reasoning: str, filter: list[str], req_settings: PromptExecutionSettings, artifact_schema: str
) -> FunctionResult:
    """Executes the actions recommended by the reasoning/planning call in the given context.

    Args:
        kernel (Kernel): The kernel object.
        reasoning (str): The reasoning from a previous model call.
        filter (list[str]): The list of plugins to INCLUDE for the tool call.
        req_settings (PromptExecutionSettings): The prompt execution settings.
        artifact (str): The artifact schema for the execution prompt.

    Returns:
        FunctionResult: The result of the execution.
    """
    filter = {"included_plugins": filter}
    req_settings.function_choice_behavior = FunctionChoiceBehavior.Auto(auto_invoke=False, filters=filter)

    kernel_function = kernel.add_function(
        prompt=execution_template,
        function_name="execution",
        plugin_name="execution",
        template_format="handlebars",
        prompt_execution_settings=req_settings,
    )

    arguments = KernelArguments(
        artifact_schema=artifact_schema,
        reasoning=reasoning,
    )

    result = await kernel.invoke(function=kernel_function, arguments=arguments)
    return result
