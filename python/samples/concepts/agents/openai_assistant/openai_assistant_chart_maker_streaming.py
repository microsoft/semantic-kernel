# Copyright (c) Microsoft. All rights reserved.
import asyncio

from samples.concepts.agents.openai_assistant.openai_assistant_sample_utils import download_response_images
from semantic_kernel.agents import AssistantAgentThread, AzureAssistantAgent
from semantic_kernel.connectors.ai.open_ai import AzureOpenAISettings
from semantic_kernel.contents import StreamingFileReferenceContent

"""
The following sample demonstrates how to create an OpenAI
assistant using either Azure OpenAI or OpenAI and leverage the
assistant and leverage the assistant's code interpreter tool
in a streaming fashion.
"""


async def main():
    # Create the client using Azure OpenAI resources and configuration
    client = AzureAssistantAgent.create_client()

    # Get the code interpreter tool and resources
    code_interpreter_tool, code_interpreter_resource = AzureAssistantAgent.configure_code_interpreter_tool()

    # Define the assistant definition
    definition = await client.beta.assistants.create(
        model=AzureOpenAISettings().chat_deployment_name,
        instructions="Create charts as requested without explanation.",
        name="ChartMaker",
        tools=code_interpreter_tool,
        tool_resources=code_interpreter_resource,
    )

    # Create the AzureAssistantAgent instance using the client and the assistant definition
    agent = AzureAssistantAgent(
        client=client,
        definition=definition,
    )

    # Create a new thread for use with the assistant
    # If no thread is provided, a new thread will be
    # created and returned with the initial response
    thread: AssistantAgentThread = None

    user_inputs = [
        """
        Display this data using a bar-chart:

        Banding  Brown Pink Yellow  Sum
        X00000   339   433     126  898
        X00300    48   421     222  691
        X12345    16   395     352  763
        Others    23   373     156  552
        Sum      426  1622     856 2904
        """,
        "Can you regenerate this same chart using the category names as the bar colors?",
    ]

    try:
        for user_input in user_inputs:
            print(f"# User: '{user_input}'")

            file_ids: list[str] = []
            is_code = False
            last_role = None
            async for response in agent.invoke_stream(messages=user_input, thread=thread):
                thread = response.thread
                current_is_code = response.metadata.get("code", False)

                if current_is_code:
                    if not is_code:
                        print("\n\n```python")
                        is_code = True
                    print(response.content, end="", flush=True)
                else:
                    if is_code:
                        print("\n```")
                        is_code = False
                        last_role = None
                    if hasattr(response, "role") and response.role is not None and last_role != response.role:
                        print(f"\n# {response.role}: ", end="", flush=True)
                        last_role = response.role
                    print(response.content, end="", flush=True)
                file_ids.extend([
                    item.file_id
                    for item in response.items
                    if isinstance(item, StreamingFileReferenceContent) and item.file_id is not None
                ])
            if is_code:
                print("```\n")

            # Use a sample utility method to download the files to the current working directory
            await download_response_images(agent, file_ids)
            file_ids.clear()

    finally:
        await thread.delete() if thread else None
        await client.beta.assistants.delete(assistant_id=agent.id)


if __name__ == "__main__":
    asyncio.run(main())
