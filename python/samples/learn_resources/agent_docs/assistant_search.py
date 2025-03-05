# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os

from semantic_kernel.agents.open_ai.azure_assistant_agent import AzureAssistantAgent
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.streaming_annotation_content import StreamingAnnotationContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.kernel import Kernel

###################################################################
# The following sample demonstrates how to create a simple,       #
# OpenAI assistant agent that utilizes the vector store           #
# to answer questions based on the uploaded documents.            #
###################################################################


def get_filepath_for_filename(filename: str) -> str:
    base_directory = os.path.dirname(os.path.realpath(__file__))
    return os.path.join(base_directory, filename)


filenames = [
    "Grimms-The-King-of-the-Golden-Mountain.txt",
    "Grimms-The-Water-of-Life.txt",
    "Grimms-The-White-Snake.txt",
]


async def main():
    agent = await AzureAssistantAgent.create(
        kernel=Kernel(),
        service_id="agent",
        name="SampleAssistantAgent",
        instructions="""
            The document store contains the text of fictional stories.
            Always analyze the document store to provide an answer to the user's question.
            Never rely on your knowledge of stories not included in the document store.
            Always format response using markdown.
            """,
        enable_file_search=True,
        vector_store_filenames=[get_filepath_for_filename(filename) for filename in filenames],
    )

    print("Creating thread...")
    thread_id = await agent.create_thread()

    try:
        is_complete: bool = False
        while not is_complete:
            user_input = input("User:> ")
            if not user_input:
                continue

            if user_input.lower() == "exit":
                is_complete = True

            await agent.add_chat_message(
                thread_id=thread_id, message=ChatMessageContent(role=AuthorRole.USER, content=user_input)
            )

            footnotes: list[StreamingAnnotationContent] = []
            async for response in agent.invoke_stream(thread_id=thread_id):
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
        print("Cleaning up resources...")
        if agent is not None:
            [await agent.delete_file(file_id) for file_id in agent.file_search_file_ids]
            await agent.delete_thread(thread_id)
            await agent.delete()


if __name__ == "__main__":
    asyncio.run(main())
