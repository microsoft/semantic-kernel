# Copyright (c) Microsoft. All rights reserved.
import asyncio

from semantic_kernel.agents import AzureResponsesAgent

"""
The following sample demonstrates how to create an OpenAI Responses Agent using either
Azure OpenAI or OpenAI. The sample shows how to have the agent answer
questions about the world.

Note, in this sample, a thread is not used. This creates a stateless agent. It will
not be able to recall previous messages, which is expected behavior.

The interaction with the agent is via the `get_response` method, which sends a
user input to the agent and receives a response from the agent. The conversation
history is maintained by the agent service, i.e. the responses are automatically
associated with the thread. Therefore, client code does not need to maintain the
conversation history.
"""

USER_INPUTS = [
    "Hi, my name is John Doe.",
    "Why is the sky blue?",
    "What is the speed of light?",
    "What is my name?",
]


async def main():
    # 1. Create the client using Azure OpenAI resources and configuration
    client, model = AzureResponsesAgent.setup_resources()

    # 2. Create a Semantic Kernel agent for the OpenAI Responses API
    agent = AzureResponsesAgent(
        ai_model_id=model,
        client=client,
        instructions="Answer questions about the world in one sentence.",
        name="Expert",
    )

    for user_input in USER_INPUTS:
        print(f"# User: '{user_input}'")
        # 3. Invoke the agent for the current message and print the response
        response = await agent.get_response(messages=user_input)
        # We are not using a thread for context, so there will be no memory
        print(f"# {response.name}: {response.content}")

    """
    You should see output similar to the following:

    # User: 'Hi, my name is John Doe.'
    # Expert: Hello, John Doe! How can I assist you today?
    # User: 'Why is the sky blue?'
    # Expert: The sky appears blue because of Rayleigh scattering, where shorter blue light wavelengths are scattered 
        more than other colors by the gases in Earth's atmosphere.
    # User: 'What is the speed of light?'
    # Expert: The speed of light in a vacuum is approximately 299,792 kilometers per second (km/s).
    # User: 'What is my name?'
    # Expert: I'm sorry, I can't determine your name from our conversation.
     """


if __name__ == "__main__":
    asyncio.run(main())
