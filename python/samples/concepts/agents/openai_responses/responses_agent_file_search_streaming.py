# Copyright (c) Microsoft. All rights reserved.
import asyncio
import os

from semantic_kernel.agents import OpenAIResponsesAgent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent

"""
The following sample demonstrates how to create an OpenAI Responses Agent.
The sample shows how to have the agent answer questions about the provided
document with streaming responses.

The interaction with the agent is via the `get_response` method, which sends a
user input to the agent and receives a response from the agent. The conversation
history is maintained by the agent service, i.e. the responses are automatically
associated with the thread. Therefore, client code does not need to maintain the
conversation history.
"""


# Simulate a conversation with the agent
USER_INPUTS = [
    "By birthday, who is the youngest employee?",
    "Who works in sales?",
    "I have a customer request, who can help me?",
]


async def main():
    # 1. Create the client using OpenAI resources and configuration
    client, model = OpenAIResponsesAgent.setup_resources()

    pdf_file_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.realpath(__file__))), "resources", "employees.pdf"
    )

    with open(pdf_file_path, "rb") as file:
        file = await client.files.create(file=file, purpose="assistants")

    vector_store = await client.vector_stores.create(
        name="step4_assistant_file_search",
        file_ids=[file.id],
    )

    file_search_tool = OpenAIResponsesAgent.configure_file_search_tool(vector_store.id)

    # 2. Create a Semantic Kernel agent for the OpenAI Responses API
    agent = OpenAIResponsesAgent(
        ai_model_id=model,
        client=client,
        instructions="Find answers to the user's questions in the provided file.",
        name="FileSearch",
        tools=[file_search_tool],
    )

    # 3. Create a thread for the agent
    # If no thread is provided, a new thread will be
    # created and returned with the initial response
    thread = None

    response_chunks: list[StreamingChatMessageContent] = []
    for user_input in USER_INPUTS:
        print(f"# User: '{user_input}'")
        # 4. Invoke the agent for the current message and print the response
        first_chunk = True
        async for response in agent.invoke_stream(messages=user_input, thread=thread):
            thread = response.thread
            response_chunks.append(response)
            if first_chunk:
                print(f"# {response.name}: ", end="", flush=True)
                first_chunk = False
            print(response.content, end="", flush=True)
        print()

    """
    # User: 'By birthday, who is the youngest employee?'
    # Agent: The youngest employee by birthday is Teodor Britton, born on January 9, 1997.
    # User: 'Who works in sales?'
    # Agent: The employees who work in sales are:

    - Mariam Jaslyn, Sales Representative
    - Hicran Bea, Sales Manager
    - Angelino Embla, Sales Representative.
    # User: 'I have a customer request, who can help me?'
    # Agent: For a customer request, you could reach out to the following people in the sales department:

    - Mariam Jaslyn, Sales Representative
    - Hicran Bea, Sales Manager
    - Angelino Embla, Sales Representative.
     """


if __name__ == "__main__":
    asyncio.run(main())
