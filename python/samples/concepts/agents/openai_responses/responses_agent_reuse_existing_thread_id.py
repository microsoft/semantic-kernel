# Copyright (c) Microsoft. All rights reserved.
import asyncio

from semantic_kernel.agents import AzureResponsesAgent
from semantic_kernel.agents.open_ai.openai_responses_agent import ResponsesAgentThread

"""
The following sample demonstrates how to create an OpenAI Responses Agent.
The sample shows how to have the agent answer questions about the world.

Once initial questions are asked, the agent will continue to answer
questions using the previous thread id. This is useful when you want to
continue a conversation with the agent without having to create a new
thread each time.
"""

USER_INPUTS = [
    "My name is John Doe.",
    "Tell me a joke",
    "Explain why this is funny.",
    "What have we been talking about?",
]


async def main():
    # 1. Create the client using Azure OpenAI resources and configuration
    client, model = AzureResponsesAgent.setup_resources()

    print(f"Using model: {model}")

    # 2. Create a Semantic Kernel agent for the OpenAI Responses API
    agent = AzureResponsesAgent(
        ai_model_id=model,
        client=client,
        instructions="Answer questions about from the user.",
        name="Joker",
    )

    # 3. Create a thread for the agent
    # If no thread is provided, a new thread will be
    # created and returned with the initial response
    thread = None

    for user_input in USER_INPUTS:
        print(f"# User: '{user_input}'")
        # 4. Invoke the agent for the current message and print the response
        response = await agent.get_response(messages=user_input, thread=thread)
        print(f"# {response.name}: {response.content}")
        # 5. Update the thread so the previous response id is used
        thread = response.thread

    # Continue with an existing thread id
    thread = ResponsesAgentThread(client=client, previous_response_id=thread.id)
    # 6. Ask the agent a new question to show the thread is still valid
    new_user_input = "What is my name?"
    print(f"# User: '{new_user_input}'")
    response = await agent.get_response(messages=new_user_input, thread=thread)
    print(f"# {response.name}: {response.content}")

    """
    You should see output similar to the following:

    # User: 'My name is John Doe.'
    # Joker: Hello, John! How can I assist you today?
    # User: 'Tell me a joke'
    # Joker: Sure! Why don't scientists trust atoms?

    Because they make up everything!
    # User: 'Explain why this is funny.'
    # Joker: The joke is funny because it plays on the double meaning of "make up." In one sense, atoms are the 
        building blocks of all matter, so they literally "make up" everything. In another sense, "make up" can mean 
        to fabricate or lie, humorously suggesting that atoms are untrustworthy because they "invent" or "fabricate" 
        everything. This clever wordplay is what makes the joke amusing.
    # User: 'What have we been talking about?'
    # Joker: We've been discussing a joke about atoms and its humor, focusing on wordplay and double meanings.
    # User: 'What is my name?'
    # Joker: Your name is John Doe.
     """


if __name__ == "__main__":
    asyncio.run(main())
