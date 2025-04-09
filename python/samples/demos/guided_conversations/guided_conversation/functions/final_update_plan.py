# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel import Kernel
from semantic_kernel.functions import FunctionResult, KernelArguments

from guided_conversation.utils.conversation_helpers import Conversation

final_update_template = """<message role="system">You are a helpful, thoughtful, and meticulous assistant. 
You just finished a conversation with a user.{{#if context}} Here is some additional context about the conversation:
{{ context }}{{/if}}

Your goal is to complete an artifact as thoroughly and accurately as possible based on the conversation.

This is the schema of the artifact:
{{ artifact_schema }}

You will be given the current state of the artifact as well as the conversation history.
Note that if the value for a field in the artifact is 'Unanswered', it means that the field was not completed. \
Some fields may have already been completed during the conversation.

Your need to determine whether there are any fields that need to be updated, and if so, update them. 
- You should only update a field if both of the following conditions are met: (a) the current state does NOT adequately reflect the conversation \
and (b) you are able to submit a valid value for a field. \
You are allowed to update completed fields, but you should only do so if the current state is inadequate, \
e.g. the user corrected a mistake in their date of birth, but the artifact does not show the corrected version. \
Remember that it's always an option to reset a field to "Unanswered" - this is often the best choice if the artifact contains incorrect information that cannot be corrected. \
Do not submit a value that is identical to the current state of the field (e.g. if the field is already "Unanswered" and the user didn't provide any new information about it, you should not submit "Unanswered"). \
- Make sure the value adheres to the constraints of the field as specified in the artifact schema. \
If it's not possible to update a field with a valid value (e.g., the user provided an invalid date of birth), you should not update the field.
- If the artifact schema is open-ended (e.g. it asks you to rate how pressing the user's issue is, without specifying rules for doing so), \
use your best judgment to determine whether you have enough information to complete the field based on the conversation. 
- Prioritize accuracy over completion. You should never make up information or make assumptions in order to complete a field. \
For example, if the field asks for a 10-digit phone number, and the user provided a 9-digit phone number, you should not add a digit to the phone number in order to complete the field.
- If the user wasn't able to provide all of the information needed to complete a field, \
use your best judgment to determine if a partial answer is appropriate (assuming it adheres to the formatting requirements of the field). \
For example, if the field asks for a description of symptoms along with details about when the symptoms started, but the user wasn't sure when their symptoms started, \
it's better to record the information they do have rather than to leave the field unanswered (and to indicate that the user was unsure about the start date).
- It's possible to update multiple fields at once (assuming you're adhering to the above rules in all cases). It's also possible that no fields need to be updated.

Your task is to state your step-by-step reasoning about what to update, followed by a final recommendation. 
Someone else will be responsible for executing the updates and they will only have access to your output \
(not any of the conversation history, artifact schema, or other context) so make sure to specify exactly which \
fields to update and the values to update them with, or to state that no fields need to be updated.
</message>

<message role="user">Conversation history:
{{ conversation_history }}

Current state of the artifact:
{{ artifact_state }}</message>"""


async def final_update_plan_function(
    kernel: Kernel,
    req_settings: dict,
    chat_history: Conversation,
    context: str,
    artifact_schema: str,
    artifact_state: str,
) -> FunctionResult:
    """This function is responsible for updating the artifact based on the conversation history when the conversation ends. This function may not always update the artifact, namely if the current state of the artifact is already accurate based on the conversation history. The function will return a step-by-step reasoning about what to update, followed by a final recommendation. The final recommendation will specify exactly which fields to update and the values to update them with, or to state that no fields need to be updated.


    Args:
        kernel (Kernel): The kernel object.
        req_settings (dict): The prompt execution settings.
        chat_history (Conversation): The conversation history.
        context (str): The context of the conversation.
        artifact_schema (str): The schema of the artifact.
        artifact_state (str): The current state of the artifact.

    Returns:
        FunctionResult: The result of the function (step-by-step reasoning about what to update in the artifact)
    """
    req_settings.tools = None
    req_settings.tool_choice = None

    # clear any extension data
    if hasattr(req_settings, "extension_data"):
        req_settings.extension_data = {}

    kernel_function = kernel.add_function(
        prompt=final_update_template,
        function_name="final_update_plan_function",
        plugin_name="final_update_plan",
        template_format="handlebars",
        prompt_execution_settings=req_settings,
    )

    arguments = KernelArguments(
        conversation_history=chat_history.get_repr_for_prompt(),
        context=context,
        artifact_schema=artifact_schema,
        artifact_state=artifact_state,
    )

    result = await kernel.invoke(function=kernel_function, arguments=arguments)

    return result
