# Copyright (c) Microsoft. All rights reserved.
import asyncio

from semantic_kernel.agents.open_ai import OpenAIAssistantAgent
from semantic_kernel.contents.file_reference_content import FileReferenceContent
from semantic_kernel.contents.streaming_file_reference_content import StreamingFileReferenceContent

#####################################################################
# The following sample demonstrates how to create an OpenAI         #
# assistant using either Azure OpenAI or OpenAI and leverage the    #
# assistant and leverage the assistant's file search functionality. #
#####################################################################

AGENT_NAME = "ChartMaker"
AGENT_INSTRUCTIONS = "Create charts as requested without explanation."

# Note: you may toggle this to switch between AzureOpenAI and OpenAI
# use_azure_openai = True

streaming = True


# A helper method to invoke the agent with the user input
async def invoke_agent(agent: OpenAIAssistantAgent, thread_id: str, input: str) -> None:
    """Invoke the agent with the user input."""
    await agent.add_chat_message(thread_id=thread_id, message=input)

    print(f"# User: '{input}'")

    if streaming:
        first_chunk = True
        async for message in agent.invoke_stream(thread_id=thread_id):
            if message.content:
                if first_chunk:
                    print(f"# {message.role}: ", end="", flush=True)
                    first_chunk = False
                print(message.content, end="", flush=True)

            if len(message.items) > 0:
                for item in message.items:
                    if isinstance(item, StreamingFileReferenceContent):
                        print(f"\n# {message.role} => {item.file_id}")
        print()
    else:
        async for message in agent.invoke(thread_id=thread_id):
            if message.content:
                print(f"# {message.role}: {message.content}")

            if len(message.items) > 0:
                for item in message.items:
                    if isinstance(item, FileReferenceContent):
                        print(f"\n`{message.role}` => {item.file_id}")


async def main():
    client = OpenAIAssistantAgent.create_openai_client()

    definition = await client.beta.assistants.create(
        model="gpt-4o",
        instructions=AGENT_INSTRUCTIONS,
        name=AGENT_NAME,
        tools=[{"type": "code_interpreter"}],
    )

    agent = OpenAIAssistantAgent(
        client=client,
        definition=definition,
    )

    # Define a thread and invoke the agent with the user input
    thread = await agent.client.beta.threads.create()

    try:
        await invoke_agent(
            agent,
            thread_id=thread.id,
            input="""
                Display this data using a bar-chart:

                Banding  Brown Pink Yellow  Sum
                X00000   339   433     126  898
                X00300    48   421     222  691
                X12345    16   395     352  763
                Others    23   373     156  552
                Sum      426  1622     856 2904
                """,
        )
        await invoke_agent(
            agent,
            thread_id=thread.id,
            input="Can you regenerate this same chart using the category names as the bar colors?",
        )
    finally:
        await agent.client.beta.threads.delete(thread.id)
        await agent.client.beta.assistants.delete(assistant_id=agent.id)


if __name__ == "__main__":
    asyncio.run(main())
