# Copyright (c) Microsoft. All rights reserved.
import asyncio
import os

from semantic_kernel.agents import OpenAIResponseAgent
from semantic_kernel.contents.chat_history import ChatHistory

"""
The following sample demonstrates how to create an OpenAI assistant using either
Azure OpenAI or OpenAI. The sample shows how to have the assistant answrer
questions about the world.

The interaction with the agent is via the `get_response` method, which sends a
user input to the agent and receives a response from the agent. The conversation
history is maintained by the agent service, i.e. the responses are automatically
associated with the thread. Therefore, client code does not need to maintain the
conversation history.
"""


# Simulate a conversation with the agent
USER_INPUTS = [
    "Who is the youngest employee?",
    "Who works in sales?",
    "I have a customer request, who can help me?",
]


async def main():
    # 1. Create the client using Azure OpenAI resources and configuration
    client, model = OpenAIResponseAgent.setup_resources()

    pdf_file_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "resources", "employees.pdf"
    )

    with open(pdf_file_path, "rb") as file:
        file = await client.files.create(file=file, purpose="assistants")

    vector_store = await client.vector_stores.create(
        name="step4_assistant_file_search",
        file_ids=[file.id],
    )

    file_search_tool = OpenAIResponseAgent.configure_file_search_tool(vector_store.id)

    # 2. Create a Semantic Kernel agent for the OpenAI Response API
    agent = OpenAIResponseAgent(
        ai_model_id=model,
        client=client,
        instructions="Find answers to the user's questions in the provided file.",
        name="FileSearch",
        tools=[file_search_tool],
    )

    # 3. Create a chat history to hold the conversation
    chat_history = ChatHistory()

    for user_input in USER_INPUTS:
        # 3. Add the user input to the chat history
        chat_history.add_user_message(user_input)
        print(f"# User: '{user_input}'")
        # 4. Invoke the agent for the current message and print the response
        first_chunk = True
        async for response in agent.invoke_stream(chat_history=chat_history):
            if first_chunk:
                print(f"# {response.name}: ", end="", flush=True)
                first_chunk = False
            print(response.content, end="", flush=True)
        print()

    """
    You should see output similar to the following:

    # User: 'Why is the sky blue?'
    # Agent: The sky appears blue because molecules in the atmosphere scatter sunlight in all directions, and blue 
        light is scattered more than other colors because it travels in shorter, smaller waves.
    # User: 'What is the speed of light?'
    # Agent: The speed of light in a vacuum is approximately 299,792,458 meters per second 
        (about 186,282 miles per second).
     """


if __name__ == "__main__":
    asyncio.run(main())
