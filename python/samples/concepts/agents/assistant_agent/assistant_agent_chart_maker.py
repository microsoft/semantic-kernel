# Copyright (c) Microsoft. All rights reserved.
import asyncio

from semantic_kernel.agents.open_ai import OpenAIAssistantAgent

#####################################################################
# The following sample demonstrates how to create an OpenAI         #
# assistant using either Azure OpenAI or OpenAI and leverage the    #
# assistant and leverage the assistant's file search functionality. #
#####################################################################

AGENT_NAME = "ChartMaker"
AGENT_INSTRUCTIONS = "Create charts as requested without explanation."

# Note: you may toggle this to switch between AzureOpenAI and OpenAI
# use_azure_openai = True

# streaming = True


# # A helper method to invoke the agent with the user input
# async def invoke_agent(agent: OpenAIAssistantAgent, thread_id: str, input: str) -> None:
#     """Invoke the agent with the user input."""
#     await agent.add_chat_message(thread_id=thread_id, message=ChatMessageContent(role=AuthorRole.USER, content=input))

#     print(f"# {AuthorRole.USER}: '{input}'")

#     if streaming:
#         first_chunk = True
#         async for message in agent.invoke_stream(thread_id=thread_id):
#             if message.content:
#                 if first_chunk:
#                     print(f"# {message.role}: ", end="", flush=True)
#                     first_chunk = False
#                 print(message.content, end="", flush=True)

#             if len(message.items) > 0:
#                 for item in message.items:
#                     if isinstance(item, StreamingFileReferenceContent):
#                         print(f"\n# {message.role} => {item.file_id}")
#         print()
#     else:
#         async for message in agent.invoke(thread_id=thread_id):
#             if message.content:
#                 print(f"# {message.role}: {message.content}")

#             if len(message.items) > 0:
#                 for item in message.items:
#                     if isinstance(item, FileReferenceContent):
#                         print(f"\n`{message.role}` => {item.file_id}")


# async def main():
#     # Create the instance of the Kernel
#     kernel = Kernel()

#     # Define a service_id for the sample
#     service_id = "agent"

#     # Create the agent configuration
#     if use_azure_openai:
#         agent = await AzureAssistantAgent.create(
#             kernel=kernel,
#             service_id=service_id,
#             name=AGENT_NAME,
#             instructions=AGENT_INSTRUCTIONS,
#             enable_code_interpreter=True,
#         )
#     else:
#         agent = await OpenAIAssistantAgent.create(
#             kernel=kernel,
#             service_id=service_id,
#             name=AGENT_NAME,
#             instructions=AGENT_INSTRUCTIONS,
#             enable_code_interpreter=True,
#         )

#     # Define a thread and invoke the agent with the user input
#     thread_id = await agent.create_thread()

#     try:
#         await invoke_agent(
#             agent,
#             thread_id=thread_id,
#             input="""
#                 Display this data using a bar-chart:

#                 Banding  Brown Pink Yellow  Sum
#                 X00000   339   433     126  898
#                 X00300    48   421     222  691
#                 X12345    16   395     352  763
#                 Others    23   373     156  552
#                 Sum      426  1622     856 2904
#                 """,
#         )
#         await invoke_agent(
#             agent,
#             thread_id=thread_id,
#             input="Can you regenerate this same chart using the category names as the bar colors?",
#         )
#     finally:
#         await agent.delete_thread(thread_id)
#         await agent.delete()


async def main():
    client = OpenAIAssistantAgent.create_openai_client()

    agent_definition = await client.beta.assistants.create(
        model="gpt-4o",
        instructions="You are a helpful assistant who answers questions about the world in one sentence.",
    )

    agent = OpenAIAssistantAgent(
        client=client,
        definition=agent_definition,
    )

    thread = await client.beta.threads.create()

    user_inputs = ["What is the weather like today?", "What is the weather like tomorrow?"]

    for user_input in user_inputs:
        print(f"# User: '{user_input}'")
        await agent.add_chat_message(
            thread_id=thread.id,
            message=user_input,
        )

        # Invoke the agent for the specified thread
        async for content in agent.invoke(thread_id=thread.id):
            print(f"# Agent: {content.content}")


if __name__ == "__main__":
    asyncio.run(main())
