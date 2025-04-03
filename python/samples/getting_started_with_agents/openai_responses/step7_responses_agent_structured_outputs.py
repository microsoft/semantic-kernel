# Copyright (c) Microsoft. All rights reserved.

import asyncio
import json

from pydantic import BaseModel

from semantic_kernel.agents import OpenAIResponsesAgent

"""
The following sample demonstrates how to create an OpenAI Responses Agent.
The sample shows how to have the agent provide response using structured outputs.

The interaction with the agent is via the `get_response` method, which sends a
user input to the agent and receives a response from the agent. The conversation
history is maintained by the chat history. Therefore, client code does need to 
maintain the conversation history if conversation context is desired.
"""

user_inputs = ["how can I solve 8x + 7y = -23, and 4x=12?"]


# Define the BaseModel we will use for structured outputs
class Step(BaseModel):
    explanation: str
    output: str


class Reasoning(BaseModel):
    steps: list[Step]
    final_answer: str


async def main():
    # 1. Create the client using OpenAI resources and configuration
    # Note: the Azure OpenAI Responses API does not yet support structured outputs.
    client, model = OpenAIResponsesAgent.setup_resources()

    # 2. Create a Semantic Kernel agent for the OpenAI Responses API
    agent = OpenAIResponsesAgent(
        ai_model_id=model,
        client=client,
        instructions="Answer the user's questions.",
        name="StructuredOutputsAgent",
        text=OpenAIResponsesAgent.configure_response_format(Reasoning),
    )

    # 3. Create a thread for the agent
    # If no thread is provided, a new thread will be
    # created and returned with the initial response
    thread = None

    for user_input in user_inputs:
        print(f"# User: {str(user_input)}")  # type: ignore
        # 5. Invoke the agent with the current chat history and print the response
        response = await agent.get_response(messages=user_input, thread=thread)
        reasoned_result = Reasoning.model_validate_json(response.message.content)
        print(f"# {response.name}:\n\n{json.dumps(reasoned_result.model_dump(), indent=4, ensure_ascii=False)}")
        thread = response.thread

    # 6. Clean up the thread
    await thread.delete() if thread else None

    """
    # User: how can I solve 8x + 7y = -23, and 4x=12?
    # StructuredOutputsAgent:

    {
        "steps": [
            {
                "explanation": "First, solve the equation 4x = 12 to find the value of x.",
                "output": "4x = 12\nx = 12 / 4\nx = 3"
            },
            {
                "explanation": "Substitute x = 3 into the first equation 8x + 7y = -23.",
                "output": "8(3) + 7y = -23"
            },
            {
                "explanation": "Perform the multiplication and simplify the equation.",
                "output": "24 + 7y = -23"
            },
            {
                "explanation": "Subtract 24 from both sides to isolate the term with y.",
                "output": "7y = -23 - 24\n7y = -47"
            },
            {
                "explanation": "Divide by 7 to solve for y.",
                "output": "y = -47 / 7\ny = -6.71 (rounded to two decimal places)"
            }
        ],
        "final_answer": "x = 3 and y = -6.71 (rounded to two decimal places)"
    }
    """


if __name__ == "__main__":
    asyncio.run(main())
