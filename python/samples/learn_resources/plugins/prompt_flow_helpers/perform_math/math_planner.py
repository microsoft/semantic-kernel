# Copyright (c) Microsoft. All rights reserved.

import asyncio

from plugins.MathPlugin.Math import Math as Math  # ignore F841
from promptflow import tool
from promptflow.connections import AzureOpenAIConnection

import semantic_kernel as sk
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, AzureTextCompletion
from semantic_kernel.planning.sequential_planner import SequentialPlanner


@tool
def my_python_tool(
    input: str,
    deployment_type: str,
    deployment_name: str,
    AzureOpenAIConnection: AzureOpenAIConnection,
) -> str:
    # Initialize the kernel
    kernel = sk.Kernel(log=sk.NullLogger())

    # Add the chat service
    if deployment_type == "chat-completion":
        kernel.add_service(
            "chat_completion",
            AzureChatCompletion(
                deployment_name,
                AzureOpenAIConnection.api_base,
                AzureOpenAIConnection.api_key,
            ),
        )
    elif deployment_type == "text-completion":
        kernel.add_service(
            "text_completion",
            AzureTextCompletion(
                deployment_name,
                AzureOpenAIConnection.api_base,
                AzureOpenAIConnection.api_key,
            ),
        )

    planner = SequentialPlanner(kernel=kernel)

    # Import the native functions
    _ = kernel.import_skill(Math(), "MathPlugin")

    ask = "Use the available math functions to solve this word problem: " + input

    plan = asyncio.run(planner.create_plan_async(ask))

    # Execute the plan
    result = asyncio.run(kernel.run_async(plan)).result

    for index, step in enumerate(plan._steps):
        print("Function: " + step.skill_name + "." + step._function.name)
        print("Input vars: " + str(step.parameters.variables))
        print("Output vars: " + str(step._outputs))
    print("Result: " + str(result))

    return str(result)
