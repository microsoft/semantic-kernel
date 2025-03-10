# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel.agents.bedrock.bedrock_agent import BedrockAgent

"""
This sample shows how to interact with a Bedrock agent via streaming in the simplest way.
This sample uses the following main component(s):
- a Bedrock agent
You will learn how to create a new Bedrock agent and talk to it.
"""

AGENT_NAME = "semantic-kernel-bedrock-agent"
INSTRUCTION = "You are a friendly assistant. You help people find information."


async def main():
    bedrock_agent = await BedrockAgent.create_and_prepare_agent(AGENT_NAME, instructions=INSTRUCTION)
    session_id = BedrockAgent.create_session_id()

    try:
        while True:
            user_input = input("User:> ")
            if user_input == "exit":
                print("\n\nExiting chat...")
                break

            # Invoke the agent
            # The chat history is maintained in the session
            print("Bedrock agent: ", end="")
            async for response in bedrock_agent.invoke_stream(
                session_id=session_id,
                input_text=user_input,
            ):
                print(response, end="")
            print()
    except KeyboardInterrupt:
        print("\n\nExiting chat...")
        return False
    except EOFError:
        print("\n\nExiting chat...")
        return False
    finally:
        # Delete the agent
        await bedrock_agent.delete_agent()

    # Sample output (using anthropic.claude-3-haiku-20240307-v1:0):
    # User:> Hi, my name is John.
    # Bedrock agent: Hello John. How can I help you?
    # User:> What is my name?
    # Bedrock agent: Your name is John.


if __name__ == "__main__":
    asyncio.run(main())
