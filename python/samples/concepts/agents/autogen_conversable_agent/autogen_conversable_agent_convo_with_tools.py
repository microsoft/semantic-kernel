# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os
from typing import Annotated, Literal

from autogen import ConversableAgent, register_function

from semantic_kernel.agents.autogen.autogen_conversable_agent import AutoGenConversableAgent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent

"""
The following sample demonstrates how to use the AutoGenConversableAgent to create a conversation between two agents
where one agent suggests a tool function call and the other agent executes the tool function call.

In this example, the assistant agent suggests a calculator tool function call to the user proxy agent. The user proxy
agent executes the calculator tool function call. The assistant agent and the user proxy agent are created using the
ConversableAgent class. The calculator tool function is registered with the assistant agent and the user proxy agent.

This sample follows the AutoGen flow outlined here:
https://microsoft.github.io/autogen/0.2/docs/tutorial/tool-use
"""


Operator = Literal["+", "-", "*", "/"]


async def main():
    def calculator(a: int, b: int, operator: Annotated[Operator, "operator"]) -> int:
        if operator == "+":
            return a + b
        if operator == "-":
            return a - b
        if operator == "*":
            return a * b
        if operator == "/":
            return int(a / b)
        raise ValueError("Invalid operator")

    assistant = ConversableAgent(
        name="Assistant",
        system_message="You are a helpful AI assistant. "
        "You can help with simple calculations. "
        "Return 'TERMINATE' when the task is done.",
        llm_config={"config_list": [{"model": "gpt-4", "api_key": os.environ["OPENAI_API_KEY"]}]},
    )

    user_proxy = ConversableAgent(
        name="User",
        llm_config=False,
        is_termination_msg=lambda msg: msg.get("content") is not None and "TERMINATE" in msg["content"],
        human_input_mode="NEVER",
    )

    assistant.register_for_llm(name="calculator", description="A simple calculator")(calculator)

    # Register the tool function with the user proxy agent.
    user_proxy.register_for_execution(name="calculator")(calculator)

    register_function(
        calculator,
        caller=assistant,  # The assistant agent can suggest calls to the calculator.
        executor=user_proxy,  # The user proxy agent can execute the calculator calls.
        name="calculator",  # By default, the function name is used as the tool name.
        description="A simple calculator",  # A description of the tool.
    )

    autogen_conversable_agent = AutoGenConversableAgent(conversable_agent=user_proxy)

    async for content in autogen_conversable_agent.invoke(
        recipient=assistant,
        message="What is (44232 + 13312 / (232 - 32)) * 5?",
        max_turns=10,
    ):
        if any(isinstance(item, FunctionResultContent) for item in content.items):
            for item in content.items:
                if isinstance(item, FunctionResultContent):
                    print(f"# {content.role} - {content.name or '*'}: '{item.result}'")
        elif any(isinstance(item, FunctionCallContent) for item in content.items):
            for item in content.items:
                if isinstance(item, FunctionCallContent):
                    print(
                        f"# {content.role} - {content.name or '*'}: Function Name: '{item.function_name}' "
                        f", Arguments: '{item.arguments}'"
                    )
        else:
            print(f"# {content.role} - {content.name or '*'}: '{content.content}'")


if __name__ == "__main__":
    asyncio.run(main())
