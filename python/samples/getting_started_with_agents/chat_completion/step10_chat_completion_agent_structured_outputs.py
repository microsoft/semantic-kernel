# Copyright (c) Microsoft. All rights reserved.

import asyncio
import json

from pydantic import BaseModel

from semantic_kernel.agents import ChatCompletionAgent, ChatHistoryAgentThread
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, AzureChatPromptExecutionSettings
from semantic_kernel.functions.kernel_arguments import KernelArguments

"""
The following sample demonstrates how to create a chat completion agent that
answers user questions using structured outputs. The `Reasoning` model is defined
on the prompt execution settings. The settings are then passed into the agent
via the `KernelArguments` object.

The interaction with the agent is via the `get_response` method, which sends a
user input to the agent and receives a response from the agent. The conversation
history needs to be maintained by the caller in the chat history object.
"""


# Define the BaseModel we will use for structured outputs
class Step(BaseModel):
    explanation: str
    output: str


class Reasoning(BaseModel):
    steps: list[Step]
    final_answer: str


# Simulate a conversation with the agent
USER_INPUT = "how can I solve 8x + 7y = -23, and 4x=12?"


async def main():
    # 1. Create the prompt settings
    settings = AzureChatPromptExecutionSettings()
    settings.response_format = Reasoning

    # 2. Create the agent by specifying the service
    agent = ChatCompletionAgent(
        service=AzureChatCompletion(),
        name="Assistant",
        instructions="Answer the user's questions.",
        arguments=KernelArguments(settings=settings),
    )

    # 3. Create a thread to hold the conversation
    # If no thread is provided, a new thread will be
    # created and returned with the initial response
    thread: ChatHistoryAgentThread = None

    print(f"# User: {USER_INPUT}")
    # 4. Invoke the agent for a response
    response = await agent.get_response(messages=USER_INPUT, thread=thread)
    # 5. Validate the response and print the structured output
    reasoned_result = Reasoning.model_validate(json.loads(response.message.content))
    print(f"# {response.name}:\n\n{reasoned_result.model_dump_json(indent=4)}")

    # 6. Cleanup: Clear the thread
    await thread.delete() if thread else None

    """
    Sample output:
    # User: how can I solve 8x + 7y = -23, and 4x=12?
    # Assistant:

    {
        "steps": [
            {
                "explanation": "The second equation 4x = 12 can be solved for x by dividing both sides by 4.",
                "output": "x = 3."
            },
            {
                "explanation": "Substitute x = 3 from the second equation into the first equation 8x + 7y = -23.",
                "output": "8(3) + 7y = -23."
            },
            {
                "explanation": "Calculate 8 times 3 to simplify the equation.",
                "output": "24 + 7y = -23."
            },
            {
                "explanation": "Subtract 24 from both sides to isolate the term with y.",
                "output": "7y = -23 - 24."
            },
            {
                "explanation": "Perform the subtraction.",
                "output": "7y = -47."
            },
            {
                "explanation": "Divide both sides by 7 to solve for y.",
                "output": "y = -47 / 7."
            },
            {
                "explanation": "Simplify the division to get the value of y.",
                "output": "y = -6.714285714285714 (approximately -6.71)."
            }
        ],
        "final_answer": "The solution to the system of equations is x = 3 and y = -6.71."
    }
    """


if __name__ == "__main__":
    asyncio.run(main())
