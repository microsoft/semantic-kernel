# Copyright (c) Microsoft. All rights reserved.

import asyncio
import json

from pydantic import BaseModel

from semantic_kernel.agents import OpenAIResponsesAgent, ResponsesAgentThread

"""
The following sample demonstrates how to create an OpenAI Response Agent.
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
    # 1. Create the client using Azure OpenAI resources and configuration
    client, model = OpenAIResponsesAgent.setup_resources()

    # 2. Create a Semantic Kernel agent for the OpenAI Response API
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
    thread: ResponsesAgentThread = None

    for user_input in user_inputs:
        print(f"# User: {str(user_input)}")  # type: ignore
        # 5. Invoke the agent with the current chat history and print the response
        response = await agent.get_response(messages=user_input, thread=thread)
        reasoned_result = Reasoning.model_validate(json.loads(str(response.content)))
        print(f"# {response.name}:\n\n{reasoned_result.model_dump_json(indent=4)}")
        thread = response.thread

    # 6. Clean up the thread
    await thread.delete() if thread else None

    """
    You should see output similar to the following:

    # User: Describe this image.
    # Agent: The image depicts a bustling scene of Times Square in New York City...

    # User: What is the main color in this image?
    # Agent: The main color in the image is blue.

    # User: Is there an animal in this image?
    # Agent: Yes, there is a cat in the image.
     """


if __name__ == "__main__":
    asyncio.run(main())
