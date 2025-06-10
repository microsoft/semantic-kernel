# Copyright (c) Microsoft. All rights reserved.

import asyncio
import os
import re

from semantic_kernel.agents import AgentGroupChat, OpenAIAssistantAgent
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole

"""
The following sample demonstrates how to create a Semantic Kernel
OpenAIAssistantAgent, and leverage the assistant's
code interpreter or file search capabilities. The user interacts
with the AI assistant by uploading files and chatting.

Note: This sample use the `AgentGroupChat` feature of Semantic Kernel, which is
no longer maintained. For a replacement, consider using the `GroupChatOrchestration`.
Read more about the `GroupChatOrchestration` here:
https://learn.microsoft.com/semantic-kernel/frameworks/agent/agent-orchestration/group-chat?pivots=programming-language-python
Here is a migration guide from `AgentGroupChat` to `GroupChatOrchestration`:
https://learn.microsoft.com/semantic-kernel/support/migration/group-chat-orchestration-migration-guide?pivots=programming-language-python
"""


# region Helper Functions


def display_intro_message():
    print(
        """
    Chat with an AI assistant backed by a Semantic Kernel OpenAIAssistantAgent.

    To start: you can upload files to the assistant using the command (brackets included):

    [upload code_interpreter | file_search file_path]

    where `code_interpreter` or `file_search` is the purpose of the file and
    `file_path` is the path to the file. For example:

    [upload code_interpreter file.txt]

    This will upload file.txt to the assistant for use with the code interpreter tool.

    Type "exit" to exit the chat.
    """
    )


def parse_upload_command(user_input: str):
    """Parse the user input for an upload command."""
    match = re.search(r"\[upload\s+(code_interpreter|file_search)\s+(.+)\]", user_input)
    if match:
        return match.group(1), match.group(2)
    return None, None


async def handle_file_upload(assistant_agent: OpenAIAssistantAgent, purpose: str, file_path: str):
    """Handle the file upload command."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    file_id = await assistant_agent.add_file(file_path, purpose="assistants")
    print(f"File uploaded: {file_id}")

    if purpose == "code_interpreter":
        await enable_code_interpreter(assistant_agent, file_id)
    elif purpose == "file_search":
        await enable_file_search(assistant_agent, file_id)


async def enable_code_interpreter(assistant_agent: OpenAIAssistantAgent, file_id: str):
    """Enable the file for code interpreter."""
    assistant_agent.code_interpreter_file_ids.append(file_id)
    tools = [{"type": "file_search"}, {"type": "code_interpreter"}]
    tool_resources = {"code_interpreter": {"file_ids": assistant_agent.code_interpreter_file_ids}}
    await assistant_agent.modify_assistant(
        assistant_id=assistant_agent.assistant.id, tools=tools, tool_resources=tool_resources
    )
    print("File enabled for code interpreter.")


async def enable_file_search(assistant_agent: OpenAIAssistantAgent, file_id: str):
    """Enable the file for file search."""
    if assistant_agent.vector_store_id is not None:
        await assistant_agent.client.beta.vector_stores.files.create(
            vector_store_id=assistant_agent.vector_store_id, file_id=file_id
        )
        assistant_agent.file_search_file_ids.append(file_id)
    else:
        vector_store = await assistant_agent.create_vector_store(file_ids=file_id)
        assistant_agent.file_search_file_ids.append(file_id)
        assistant_agent.vector_store_id = vector_store.id
        tools = [{"type": "file_search"}, {"type": "code_interpreter"}]
        tool_resources = {"file_search": {"vector_store_ids": [vector_store.id]}}
        await assistant_agent.modify_assistant(
            assistant_id=assistant_agent.assistant.id, tools=tools, tool_resources=tool_resources
        )
    print("File enabled for file search.")


async def cleanup_resources(assistant_agent: OpenAIAssistantAgent):
    """Cleanup the resources used by the assistant."""
    if assistant_agent.vector_store_id:
        await assistant_agent.delete_vector_store(assistant_agent.vector_store_id)
    for file_id in assistant_agent.code_interpreter_file_ids:
        await assistant_agent.delete_file(file_id)
    for file_id in assistant_agent.file_search_file_ids:
        await assistant_agent.delete_file(file_id)
    await assistant_agent.delete()


# endregion


async def main():
    assistant_agent = None
    try:
        display_intro_message()

        # Create the OpenAI Assistant Agent
        assistant_agent = await OpenAIAssistantAgent.create(
            service_id="AIAssistant",
            description="An AI assistant that helps with everyday tasks.",
            instructions="Help the user with their task.",
            enable_code_interpreter=True,
            enable_file_search=True,
        )

        # Define an agent group chat, which drives the conversation
        # We add messages to the chat and then invoke the agent to respond.
        chat = AgentGroupChat()

        while True:
            try:
                user_input = input("User:> ")
            except (KeyboardInterrupt, EOFError):
                print("\n\nExiting chat...")
                break

            if user_input.strip().lower() == "exit":
                print("\n\nExiting chat...")
                break

            purpose, file_path = parse_upload_command(user_input)
            if purpose and file_path:
                await handle_file_upload(assistant_agent, purpose, file_path)
                continue

            await chat.add_chat_message(message=ChatMessageContent(role=AuthorRole.USER, content=user_input))
            async for content in chat.invoke(agent=assistant_agent):
                print(f"Assistant:> # {content.role} - {content.name or '*'}: '{content.content}'")
    finally:
        if assistant_agent:
            await cleanup_resources(assistant_agent)


if __name__ == "__main__":
    asyncio.run(main())
