# Copyright (c) Microsoft. All rights reserved.

import asyncio

import boto3

from semantic_kernel.agents.bedrock.bedrock_agent import BedrockAgent

"""
The following sample demonstrates how to use an already existing
Bedrock Agent within Semantic Kernel. This sample requires that you
have an existing agent created either previously in code or via the
AWS Console.
This sample uses the following main component(s):
- a Bedrock agent
You will learn how to retrieve a Bedrock agent and talk to it.
"""

# Replace "your-agent-id" with the ID of the agent you want to use
AGENT_ID = "your-agent-id"


async def main():
    client = boto3.client("bedrock-agent")
    agent_model = client.get_agent(agentId=AGENT_ID)["agent"]
    bedrock_agent = BedrockAgent(agent_model)
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
