# Copyright (c) Microsoft. All rights reserved.
import asyncio
import os

from semantic_kernel.agents.openai.open_ai_assistant_agent import OpenAIAssistantAgent
from semantic_kernel.agents.openai.open_ai_assistant_definition import OpenAIAssistantDefinition
from semantic_kernel.agents.openai.open_ai_service_configuration import OpenAIServiceConfiguration
from semantic_kernel.agents.openai.open_ai_thread_creation_options import OpenAIThreadCreationOptions
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.kernel import Kernel

AGENT_NAME = "CodeRunner"
AGENT_INSTRUCTIONS = "Run the provided code file and return the result."


# A helper method to invoke the agent with the user input
async def invoke_agent(agent: OpenAIAssistantAgent, thread_id: str, input: str) -> None:
    """Invoke the agent with the user input."""
    await agent.add_chat_message(thread_id=thread_id, message=ChatMessageContent(role=AuthorRole.USER, content=input))

    print(f"# {AuthorRole.USER}: '{input}'")

    async for content in agent.invoke(thread_id=thread_id):
        if content.role != AuthorRole.TOOL:
            print(f"# {content.role}: {content.content}")


async def main():
    # Create the instance of the Kernel
    kernel = Kernel()

    # Add the OpenAIChatCompletion AI Service to the Kernel
    service_id = "agent"

    # Create the agent
    configuration = OpenAIServiceConfiguration.for_openai(service_id=service_id)
    definition = OpenAIAssistantDefinition(
        name=AGENT_NAME, instructions=AGENT_INSTRUCTIONS, enable_code_interpreter=True
    )

    agent = OpenAIAssistantAgent(kernel=kernel, configuration=configuration, definition=definition)

    await agent.create_assistant()

    code_file_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.realpath(__file__))),
        "resources",
        "agent_assistant_code_interpreter_file",
        "fibonacci.py",
    )

    file_id = await agent.add_file(code_file_path, purpose="assistants")

    thread_options = OpenAIThreadCreationOptions(code_interpreter_file_ids=[file_id])

    thread_id = await agent.create_thread(thread_options)

    try:
        await invoke_agent(
            agent, thread_id=thread_id, input="Use code interpreter to run the provided file and give me the result"
        )
    finally:
        await agent.delete_thread(thread_id)
        await agent.delete()


if __name__ == "__main__":
    asyncio.run(main())
