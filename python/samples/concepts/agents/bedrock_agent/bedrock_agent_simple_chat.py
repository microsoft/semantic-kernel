# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel.agents import BedrockAgent, BedrockAgentThread

"""
This sample shows how to interact with a Bedrock agent in the simplest way.
This sample uses the following main component(s):
- a Bedrock agent
You will learn how to create a new Bedrock agent and talk to it.
"""

AGENT_NAME = "semantic-kernel-bedrock-agent"
INSTRUCTION = "You are a friendly assistant. You help people find information."


async def main():
    bedrock_agent = await BedrockAgent.create_and_prepare_agent(AGENT_NAME, instructions=INSTRUCTION)

    # Create a thread for the agent
    # If no thread is provided, a new thread will be
    # created and returned with the initial response
    thread: BedrockAgentThread = None

    try:
        while True:
            user_input = input("User:> ")
            if user_input == "exit":
                print("\n\nExiting chat...")
                break

            # Invoke the agent
            # The chat history is maintained in the session
            response = await bedrock_agent.get_response(
                messages=user_input,
                thread=thread,
            )
            print(f"Bedrock agent: {response}")
            thread = response.thread
    except KeyboardInterrupt:
        print("\n\nExiting chat...")
        return False
    except EOFError:
        print("\n\nExiting chat...")
        return False
    finally:
        # Delete the agent
        await bedrock_agent.delete_agent()
        await thread.delete() if thread else None

    # Sample output (using anthropic.claude-3-haiku-20240307-v1:0):
    # User:> Hi, my name is John.
    # Bedrock agent: Hello John. How can I help you?
    # User:> What is my name?
    # Bedrock agent: Your name is John.


if __name__ == "__main__":
    asyncio.run(main())
