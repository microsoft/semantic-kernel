# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

from semantic_kernel.agents.open_ai import AzureAssistantAgent
from semantic_kernel.contents import StreamingAnnotationContent

"""
The following sample demonstrates how to create a simple,
OpenAI assistant agent that utilizes the vector store
to answer questions based on the uploaded documents.

This is the full code sample for the Semantic Kernel Learn Site: How-To: Open AI Assistant Agent File Search

https://learn.microsoft.com/semantic-kernel/frameworks/agent/examples/example-assistant-search?pivots=programming-language-python
"""


def get_filepath_for_filename(filename: str) -> str:
    base_directory = os.path.join(
        os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
        "resources",
    )
    return os.path.join(base_directory, filename)


filenames = [
    "Grimms-The-King-of-the-Golden-Mountain.txt",
    "Grimms-The-Water-of-Life.txt",
    "Grimms-The-White-Snake.txt",
]


async def main():
    # Create the client using Azure OpenAI resources and configuration
    client, model = AzureAssistantAgent.setup_resources()

    # Upload the files to the client
    file_ids: list[str] = []
    for path in [get_filepath_for_filename(filename) for filename in filenames]:
        with open(path, "rb") as file:
            file = await client.files.create(file=file, purpose="assistants")
            file_ids.append(file.id)

    vector_store = await client.beta.vector_stores.create(
        name="assistant_search",
        file_ids=file_ids,
    )

    # Get the file search tool and resources
    file_search_tools, file_search_tool_resources = AzureAssistantAgent.configure_file_search_tool(
        vector_store_ids=vector_store.id
    )

    # Create the assistant definition
    definition = await client.beta.assistants.create(
        model=model,
        instructions="""
            The document store contains the text of fictional stories.
            Always analyze the document store to provide an answer to the user's question.
            Never rely on your knowledge of stories not included in the document store.
            Always format response using markdown.
            """,
        name="SampleAssistantAgent",
        tools=file_search_tools,
        tool_resources=file_search_tool_resources,
    )

    # Create the agent using the client and the assistant definition
    agent = AzureAssistantAgent(
        client=client,
        definition=definition,
    )

    print("Creating thread...")
    thread = await client.beta.threads.create()

    try:
        is_complete: bool = False
        while not is_complete:
            user_input = input("User:> ")
            if not user_input:
                continue

            if user_input.lower() == "exit":
                is_complete = True
                break

            await agent.add_chat_message(thread_id=thread.id, message=user_input)

            footnotes: list[StreamingAnnotationContent] = []
            async for response in agent.invoke_stream(thread_id=thread.id):
                footnotes.extend([item for item in response.items if isinstance(item, StreamingAnnotationContent)])

                print(f"{response.content}", end="", flush=True)

            print()

            if len(footnotes) > 0:
                for footnote in footnotes:
                    print(
                        f"\n`{footnote.quote}` => {footnote.file_id} "
                        f"(Index: {footnote.start_index} - {footnote.end_index})"
                    )

    finally:
        print("\nCleaning up resources...")
        [await client.files.delete(file_id) for file_id in file_ids]
        await client.beta.threads.delete(thread.id)
        await client.beta.assistants.delete(agent.id)


if __name__ == "__main__":
    asyncio.run(main())
