# Copyright (c) Microsoft. All rights reserved.
import asyncio

from semantic_kernel.agents import OpenAIResponsesAgent

"""
The following sample demonstrates how to create an OpenAI Responses Agent.
The sample shows how to have the agent answer questions using the web search
preview tool with streaming responses.

The interaction with the agent is via the `get_response` method, which sends a
user input to the agent and receives a response from the agent. The conversation
history is maintained by the agent service, i.e. the responses are automatically
associated with the thread. Therefore, client code does not need to maintain the
conversation history.
"""


# Simulate a conversation with the agent
USER_INPUTS = [
    "Find me news articles about the latest technology trends.",
]


async def main():
    # 1. Create the client using OpenAI resources and configuration
    client, model = OpenAIResponsesAgent.setup_resources()

    web_search_tool = OpenAIResponsesAgent.configure_web_search_tool()

    # 2. Create a Semantic Kernel agent for the OpenAI Responses API
    agent = OpenAIResponsesAgent(
        ai_model_id=model,
        client=client,
        instructions="Answer questions from the user.",
        name="Host",
        tools=[web_search_tool],
    )

    # 3. Create a thread for the agent
    # If no thread is provided, a new thread will be
    # created and returned with the initial response
    thread = None

    for user_input in USER_INPUTS:
        print(f"# User: '{user_input}'")
        # 4. Invoke the agent for the current message and print the response
        first_chunk = True
        async for response in agent.invoke_stream(messages=user_input, thread=thread):
            thread = response.thread
            if first_chunk:
                print(f"# {response.name}: ", end="", flush=True)
                first_chunk = False
            print(response.content, end="", flush=True)
        print()

    """
    You should see output similar to the following:

    # User: 'Find me news articles about the latest technology trends.'
    # NewsSearcher: Recent developments in technology have highlighted several key trends shaping various industries:

    **Artificial Intelligence (AI) Integration**: AI continues to revolutionize sectors by automating tasks, 
        enhancing real-time analytics, and improving content delivery. At the 2025 NAB Show, AI's influence is 
        evident across creator platforms, sports technology, streaming solutions, and cloud architectures. 
        ([tvtechnology.com](https://www.tvtechnology.com/news/nab-show-2025-exhibitor-insight-black-box?utm_source=openai))
    ...
    """


if __name__ == "__main__":
    asyncio.run(main())
