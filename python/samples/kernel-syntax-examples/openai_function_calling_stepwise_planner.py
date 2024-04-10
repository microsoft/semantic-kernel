# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.core_plugins.math_plugin import MathPlugin
from semantic_kernel.core_plugins.time_plugin import TimePlugin
from semantic_kernel.planners.function_calling_stepwise_planner.function_calling_stepwise_planner import (
    FunctionCallingStepwisePlanner,
)
from semantic_kernel.planners.function_calling_stepwise_planner.function_calling_stepwise_planner_options import (
    FunctionCallingStepwisePlannerOptions,
)


def get_initial_plan() -> str:
    return """
template_format: semantic-kernel
template: |
    <message role="system">
    You are an expert at generating plans from a given GOAL. Think step by step and determine a plan to satisfy the specified GOAL using only the FUNCTIONS provided to you. You can also make use of your own knowledge while forming an answer but you must not use functions that are not provided. Once you have come to a final answer, use the UserInteraction{{$name_delimiter}}SendFinalAnswer function to communicate this back to the user.

    [FUNCTIONS]

    {{$available_functions}}

    [END FUNCTIONS]

    To create the plan, follow these steps:
    0. Each step should be something that is capable of being done by the list of available functions.
    1. Steps can use output from one or more previous steps as input, if appropriate.
    2. The plan should be as short as possible.
    3. Make use of other asks from the user.
    </message>
    <message role="user">{{$goal}}</message>
    {{$chat_history}}
description: Generate a step-by-step plan to satisfy a given goal
name: GeneratePlan
input_variables:
  - name: available_functions
    description: A list of functions that can be used to generate the plan
  - name: goal
    description: The goal to satisfy
execution_settings:
  default:
    temperature: 0.0
    top_p: 0.0
    presence_penalty: 0.0
    frequency_penalty: 0.0
    max_tokens: 256
    stop_sequences: []
""".strip()  # noqa: E501


def get_step_prompt() -> str:
    return """
{{$chat_history}}

Original request: {{$goal}}

You are in the process of helping the user fulfill this request using the following plan:
{{$initial_plan}}

The user will ask you for help with each step.
""".strip()


async def main():
    kernel = sk.Kernel()

    service_id = "planner"
    api_key, _ = sk.openai_settings_from_dot_env()
    kernel.add_service(
        OpenAIChatCompletion(
            service_id=service_id,
            ai_model_id="gpt-3.5-turbo-1106",
            api_key=api_key,
        ),
    )

    cur_dir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "resources")
    kernel.import_native_plugin_from_directory(cur_dir, "email_plugin")

    kernel.import_plugin_from_object(MathPlugin(), "MathPlugin")
    kernel.import_plugin_from_object(TimePlugin(), "TimePlugin")

    questions = [
        "What is the current hour number, plus 5?",
        "What is 387 minus 22? Email the solution to John and Mary.",
        "Write a limerick, translate it to Spanish, and send it to Jane",
    ]

    options = FunctionCallingStepwisePlannerOptions(
        max_iterations=10,
        max_tokens=4000,
        get_initial_plan=get_initial_plan,
        get_step_prompt=get_step_prompt,
    )

    chat_history = ChatHistory()
    chat_history.add_user_message("You must respond to every ask like a parrot.")

    planner = FunctionCallingStepwisePlanner(service_id=service_id, options=options)

    for question in questions:
        result = await planner.invoke(kernel, question, chat_history=chat_history)
        print(f"Q: {question}\nA: {result.final_answer}\n")

        # Uncomment the following line to view the planner's process for completing the request
        # print(f"Chat history: {result.chat_history}\n")


if __name__ == "__main__":
    asyncio.run(main())
