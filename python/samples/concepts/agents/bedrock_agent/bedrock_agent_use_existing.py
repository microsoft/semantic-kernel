# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel.agents.bedrock.bedrock_agent import BedrockAgent

# This sample shows how to interact with a Bedrock agent in the simplest way.
# This sample uses the following main component(s):
# - a Bedrock agent that has already been created
# You will learn how to connect to an existing Bedrock agent and talk to it.


# Make sure to replace AGENT_NAME and AGENT_ID with the correct values
AGENT_NAME = "semantic-kernel-bedrock-agent"
AGENT_ID = "..."


async def main():
    bedrock_agent = await BedrockAgent.retrieve(AGENT_ID, AGENT_NAME)
    session_id = BedrockAgent.create_session_id()

    try:
        while True:
            user_input = input("User:> ")
            if user_input == "exit":
                print("\n\nExiting chat...")
                break

            # Invoke the agent
            # The chat history is maintained in the session
            async for response in bedrock_agent.invoke(
                session_id=session_id,
                input_text=user_input,
            ):
                print(f"Bedrock agent: {response}")
    except KeyboardInterrupt:
        print("\n\nExiting chat...")
        return False
    except EOFError:
        print("\n\nExiting chat...")
        return False

    # Sample output (using anthropic.claude-3-haiku-20240307-v1:0):
    # User:> Hi, my name is John.
    # Bedrock agent: Hello John. How can I help you?
    # User:> What is my name?
    # Bedrock agent: Your name is John.


if __name__ == "__main__":
    asyncio.run(main())
