# Copyright (c) Microsoft. All rights reserved.

import asyncio

from semantic_kernel.agents.bedrock.bedrock_agent import BedrockAgent

# This sample shows how to update an existing Bedrock agent.
# This sample uses the following main component(s):
# - a Bedrock agent
# You will learn how to connect to a Bedrock agent and update its properties.


# Make sure to replace AGENT_NAME and AGENT_ID with the correct values
AGENT_NAME = "semantic-kernel-bedrock-agent"
INSTRUCTION = "You are a friendly assistant but you don't know anything about AI."
NEW_INSTRUCTION = "You are a friendly assistant and you know a lot about AI."


async def main():
    bedrock_agent = await BedrockAgent.create(AGENT_NAME, instructions=INSTRUCTION)

    async def ask_about_ai():
        session_id = BedrockAgent.create_session_id()
        async for response in bedrock_agent.invoke(
            session_id=session_id,
            input_text="What is AI in one sentence?",
        ):
            print(response)

    try:
        print("Before updating the agent:")
        await ask_about_ai()

        await bedrock_agent.update_agent(instruction=NEW_INSTRUCTION)

        print("After updating the agent:")
        await ask_about_ai()
    finally:
        # Delete the agent
        await bedrock_agent.delete_agent()

    # Sample output (using anthropic.claude-3-haiku-20240307-v1:0):
    # Before updating the agent:
    # I apologize, but I do not have any information about AI or the ability to define it.
    # As I mentioned, I am a friendly assistant without any knowledge about AI. I cannot
    # provide a definition for AI in one sentence. If you have a different question I can
    # try to assist with, please let me know.
    # After updating the agent:
    # AI is the field of computer science that aims to create systems and machines that can
    # perform tasks that typically require human intelligence, such as learning, problem-solving,
    # perception, and decision-making.


if __name__ == "__main__":
    asyncio.run(main())
