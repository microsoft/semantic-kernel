# Copyright (c) Microsoft. All rights reserved.

import logging

from semantic_kernel import Kernel
from semantic_kernel.functions import FunctionResult, KernelArguments

from guided_conversation.plugins.agenda import Agenda
from guided_conversation.plugins.artifact import Artifact
from guided_conversation.utils.conversation_helpers import Conversation
from guided_conversation.utils.resources import GCResource, ResourceConstraintMode

logger = logging.getLogger(__name__)

conversation_plan_template = """<message role="system">You are a helpful, thoughtful, and meticulous assistant.
You are conducting a conversation with a user. \
Your goal is to complete an artifact as thoroughly as possible by the end of the conversation, and to ensure a smooth experience for the user.

This is the schema of the artifact you are completing:
{{ artifact_schema }}{{#if context}}

Here is some additional context about the conversation:
{{ context }}{{/if}}

Throughout the conversation, you must abide by these rules:
{{ rules }}{{#if current_state_description }}

Here's a description of the conversation flow:
{{ current_state_description }}
Follow this description, and exercise good judgment about when it is appropriate to deviate.{{/if}}

You will be provided the history of your conversation with the user up until now and the current state of the artifact.
Note that if the value for a field in the artifact is 'Unanswered', it means that the field has not been completed.
You need to select the best possible action(s), given the state of the conversation and the artifact.
These are the possible actions you can take:
{{#if show_agenda}}Update agenda (required parameters: items)
- If the latest agenda is set to "None", you should always pick this action.
- You should pick this action if you need to change your plan for the conversation to make the best use of the remaining turns available to you. \
Consider how long it usually takes to get the information you need (which is a function of the quality and pace of the user's responses), \
the number, complexity, and importance of the remaining fields in the artifact, and the number of turns remaining ({{ remaining_resource }}). \
Based on these factors, you might need to accelerate (e.g. combine several topics) or slow down the conversation (e.g. spread out a topic), in which case you should update the agenda accordingly. \
Note that skipping an artifact field is NOT a valid way to accelerate the conversation.
- You must provide an ordered list of items to be completed sequentially, where the first item contains everything you will do in the current turn of the conversation (in addition to updating the agenda). \
For example, if you choose to send a message to the user asking for their name and medical history, then you would write "ask for name and medical history" as the first item. \
If you think medical history will take longer than asking for the name, then you would write "complete medical history" as the second item, with an estimate of how many turns you think it will take. \
Do NOT include items that have already been completed. \
Items must always represent a conversation topic (corresponding to the "Send message to user" action). Updating the artifact (e.g. "update field X based on the discussion") or terminating the conversation is NOT a valid item.
- The latest agenda was created in the previous turn of the conversation. \
Even if the total turns in the latest agenda equals the remaining turns, you should still update the agenda if you think the current plan is suboptimal (e.g. the first item was completed, the order of items is not ideal, an item is too broad or not a conversation topic, etc.). 
- Each item must have a description and and your best guess for the number of turns required to complete it. Do not provide a range of turns. \
It is EXTREMELY important that the total turns allocated across all items in the updated agenda (including the first item for the current turn) {{ total_resource_str }} \
Everything in the agenda should be something you expect to complete in the remaining turns - there shouldn't be any optional "buffer" items. \
It can be helpful to include the cumulative turns allocated for each item in the agenda to ensure you adhere to this rule, e.g. item 1 = 2 turns (cumulative total = 2), item 2 = 4 turns (cumulative total = 6), etc.
- Avoid high-level items like "ask follow-up questions" - be specific about what you need to do.
- Do NOT include wrap-up items such as "review and confirm all information with the user" (you should be doing this throughout the conversation) or "thank the user for their time". \
Do NOT repeat topics that have already been sufficiently addressed. {{ ample_time_str }}{{/if}}

Send message to user (required parameters: message)
- If there is no conversation history, you should always pick this action.
- You should pick this action if (a) the user asked a question or made a statement that you need to respond to, \
or (b) you need to follow-up with the user because the information they provided is incomplete, invalid, ambiguous, or in some way insufficient to complete the artifact. \
For example, if the artifact schema indicates that the "date of birth" field must be in the format "YYYY-MM-DD", but the user has only provided the month and year, you should send a message to the user asking for the day. \
Likewise, if the user claims that their date of birth is February 30, you should send a message to the user asking for a valid date. \
If the artifact schema is open-ended (e.g. it asks you to rate how pressing the user's issue is, without specifying rules for doing so), use your best judgment to determine whether you have enough information or you need to continue probing the user. \
It's important to be thorough, but also to avoid asking the user for unnecessary information.

Update artifact fields (required parameters: field, value)
- You should pick this action as soon as (a) the user provides new information that is not already reflected in the current state of the artifact and (b) you are able to submit a valid value for a field in the artifact using this new information. \
If you have already updated a field in the artifact and there is no new information to update the field with, you should not pick this action.
- Make sure the value adheres to the constraints of the field as specified in the artifact schema.
- If the user has provided all required information to complete a field (i.e. the criteria for "Send message to user" are not satisfied) but the information is in the wrong format, you should not ask the user to reformat their response. \
Instead, you should simply update the field with the correctly formatted value. For example, if the artifact asks for the date of birth in the format "YYYY-MM-DD", and the user provides their date of birth as "June 15, 2000", you should update the field with the value "2000-06-15".
- Prioritize accuracy over completion. You should never make up information or make assumptions in order to complete a field. \
For example, if the field asks for a 10-digit phone number, and the user provided a 9-digit phone number, you should not add a digit to the phone number in order to complete the field. \
Instead, you should follow-up with the user to ask for the correct phone number. If they still aren't able to provide one, you should leave the field unanswered.
- If the user isn't able to provide all of the information needed to complete a field, \
use your best judgment to determine if a partial answer is appropriate (assuming it adheres to the formatting requirements of the field). \
For example, if the field asks for a description of symptoms along with details about when the symptoms started, but the user isn't sure when their symptoms started, \
it's better to record the information they do have rather than to leave the field unanswered (and to indicate that the user was unsure about the start date).
- If it's possible to update multiple fields at once (assuming you're adhering to the above rules in all cases), you should do so. \
For example, if the user provides their full name and date of birth in the same message, you should select the "update artifact fields" action twice, once for each field.

End conversation (required parameters: None)
{{ termination_instructions }}
{{ resource_instructions }}

If you select the "Update artifact field" action or the "Update agenda" action, you should also select one of the "Send message to user" or "End conversation" actions. \
Note that artifact and updates updates will always be executed before a message is sent to the user or the conversation is terminated. \
Also note that only one message can be sent to the user at a time.

Your task is to state your step-by-step reasoning for the best possible action(s), followed by a final recommendation of which action(s) to take, including all required parameters.
Someone else will be responsible for executing the action(s) you select and they will only have access to your output \
(not any of the conversation history, artifact schema, or other context) so it is EXTREMELY important \
that you clearly specify the value of all required parameters for each action you select.</message>

<message role="user">Conversation history:
{{ chat_history }}

Latest agenda:
{{ agenda_state }}

Current state of the artifact:
{{ artifact_state }}</message>"""


async def conversation_plan_function(
    kernel: Kernel,
    chat_history: Conversation,
    context: str,
    rules: list[str],
    conversation_flow: str,
    current_artifact: Artifact,
    req_settings: dict,
    resource: GCResource,
    agenda: Agenda,
) -> FunctionResult:
    """Reasons/plans about the next best action(s) to continue the conversation. In this function, a DESCRIPTION of the possible actions
    are surfaced to the agent. Note that the agent will not execute the actions, but will provide a step-by-step reasoning for the best
    possible action(s). The implication here is that NO tool/plugin calls are made, only a description of what tool calls might be called
    is created.

    Currently, the reasoning/plan from this function is passed to another function (which leverages openai tool calling) that will execute
    the actions.

    Args:
        kernel (Kernel): The kernel object.
        chat_history (Conversation): The conversation history
        context (str): Creator provided context of the conversation
        rules (list[str]): Creator provided rules
        conversation_flow (str): Creator provided conversation flow
        current_artifact (Artifact): The current artifact
        req_settings (dict): The request settings
        resource (GCResource): The resource object

    Returns:
        FunctionResult: The function result.
    """
    # clear any pre-existing tools from the request settings
    req_settings.tools = None
    req_settings.tool_choice = None

    # clear any extension data
    if hasattr(req_settings, "extension_data"):
        req_settings.extension_data = {}

    kernel_function = kernel.add_function(
        prompt=conversation_plan_template,
        function_name="conversation_plan_function",
        plugin_name="conversation_plan",
        template_format="handlebars",
        prompt_execution_settings=req_settings,
    )

    remaining_resource = resource.remaining_units
    resource_instructions = resource.get_resource_instructions()

    # if there is a resource constraint and there's more than one turn left, include the update agenda action
    if (resource_instructions != "") and (remaining_resource > 1):
        if resource.get_resource_mode() == ResourceConstraintMode.MAXIMUM:
            total_resource_str = f"does not exceed the remaining turns ({remaining_resource})."
            ample_time_str = ""
        elif resource.get_resource_mode() == ResourceConstraintMode.EXACT:
            total_resource_str = (
                f"is equal to the remaining turns ({remaining_resource}). Do not leave any turns unallocated."
            )
            ample_time_str = """If you have many turns remaining, instead of including wrap-up items or repeating topics, you should include items that increase the breadth and/or depth of the conversation \
in a way that's directly relevant to the artifact (e.g. "collect additional details about X", "ask for clarification about Y", "explore related topic Z", etc.)."""
        else:
            logger.error("Invalid resource mode.")
    else:
        total_resource_str = ""
        ample_time_str = ""
    termination_instructions = _get_termination_instructions(resource)

    # only include the agenda if there is a resource constraint and there's more than one turn left
    show_agenda = resource_instructions != "" and remaining_resource > 1

    arguments = KernelArguments(
        context=context,
        artifact_schema=current_artifact.get_schema_for_prompt(),
        rules=" ".join([r.strip() for r in rules]),
        current_state_description=conversation_flow,
        show_agenda=show_agenda,
        remaining_resource=remaining_resource,
        total_resource_str=total_resource_str,
        ample_time_str=ample_time_str,
        termination_instructions=termination_instructions,
        resource_instructions=resource_instructions,
        chat_history=chat_history.get_repr_for_prompt(),
        agenda_state=agenda.get_agenda_for_prompt(),
        artifact_state=current_artifact.get_artifact_for_prompt(),
    )

    result = await kernel.invoke(function=kernel_function, arguments=arguments)
    return result


def _get_termination_instructions(resource: GCResource):
    """
    Get the termination instructions for the conversation. This is contingent on the resources mode,
    if any, that is available.

    Assumes we're always using turns as the resource unit.

    Args:
        resource (GCResource): The resource object.

    Returns:
        str: the termination instructions
    """
    # Termination condition under no resource constraints
    if resource.resource_constraint is None:
        return "- You should pick this action as soon as you have completed the artifact to the best of your ability, \
the conversation has come to a natural conclusion, or the user is not cooperating so you cannot continue the conversation."

    # Termination condition under exact resource constraints
    if resource.resource_constraint.mode == ResourceConstraintMode.EXACT:
        return (
            "- You should only pick this action if the user is not cooperating so you cannot continue the conversation."
        )

    # Termination condition under maximum resource constraints
    elif resource.resource_constraint.mode == ResourceConstraintMode.MAXIMUM:
        return "- You should pick this action as soon as you have completed the artifact to the best of your ability, \
the conversation has come to a natural conclusion, or the user is not cooperating so you cannot continue the conversation."

    else:
        logger.error("Invalid resource mode provided.")
        return ""
