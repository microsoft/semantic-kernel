# Copyright (c) Microsoft. All rights reserved.

import chainlit as cl

from samples.demos.agent_orchestration_chainlit.custom_agents import AgentFactory
from samples.demos.agent_orchestration_chainlit.custom_group_chat_manager import CustomGroupChatManager
from semantic_kernel.agents import Agent, GroupChatOrchestration
from semantic_kernel.agents.orchestration.orchestration_base import OrchestrationResult
from semantic_kernel.agents.runtime.in_process.in_process_runtime import InProcessRuntime
from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import AzureChatCompletion
from semantic_kernel.contents import ChatHistory, ChatMessageContent, StreamingChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole

SAMPLE_TASK = "A link where I can directly download the latest Microsoft 10k pdf file"


async def streaming_agent_response_callback(message_chunk: StreamingChatMessageContent, is_final: bool) -> None:
    streaming_handler = cl.user_session.get("streaming_handler")
    if streaming_handler is None:
        streaming_handler = cl.Message("", author=message_chunk.name)
        cl.user_session.set("streaming_handler", streaming_handler)

    await streaming_handler.stream_token(message_chunk.content)
    if is_final:
        await streaming_handler.send()
        cl.user_session.set("streaming_handler", None)


async def human_response_function(chat_histoy: ChatHistory) -> ChatMessageContent:
    """Function to get user input."""
    user_input = await cl.AskUserMessage("Please provide your input", author="Group Manager").send()
    return ChatMessageContent(
        role=AuthorRole.USER, content=user_input["output"] if user_input else "No input provided."
    )


async def get_group_chat_orchestration(agents: list[Agent]) -> GroupChatOrchestration:
    """Return a GroupChatOrchestration instance with the agents and custom manager."""
    return GroupChatOrchestration(
        members=agents,
        # max_rounds is odd, so that the writer gets the last round
        manager=CustomGroupChatManager(
            chat_completion_service=AzureChatCompletion(),
            max_rounds=5,
            human_response_function=human_response_function,
        ),
        streaming_agent_response_callback=streaming_agent_response_callback,
    )


async def setup_runnable():
    # Setup the user session with the orchestration and chat history
    if cl.user_session.get("agent_factory") is None:
        agent_factory = AgentFactory()
        cl.user_session.set("agent_factory", agent_factory)

    agent_factory: AgentFactory = cl.user_session.get("agent_factory")
    azure_ai_search_agent = await agent_factory.create_azure_ai_search_agent()

    orchestration = await get_group_chat_orchestration([
        azure_ai_search_agent,
    ])
    cl.user_session.set("orchestration", orchestration)

    runtime = InProcessRuntime()
    runtime.start()
    cl.user_session.set("runtime", runtime)

    print("Group chat orchestration setup complete.")


@cl.password_auth_callback
def auth_callback(username: str, password: str):
    # Fetch the user matching username from your database
    # and compare the hashed password with the value stored in the database
    if (username, password) == ("admin", "admin"):
        return cl.User(identifier="admin", metadata={"role": "admin", "provider": "credentials"})
    return None


@cl.on_chat_start
async def on_chat_start():
    await setup_runnable()


@cl.on_chat_end
async def on_chat_end():
    """Cleanup resources when the chat ends."""
    agent_factory: AgentFactory = cl.user_session.get("agent_factory")
    if agent_factory:
        await agent_factory.cleanup()

    runtime: InProcessRuntime = cl.user_session.get("runtime")
    if runtime:
        await runtime.close()

    print("Chat ended, resources cleaned up.")


@cl.on_message
async def on_message(msg: cl.Message):
    """Handle incoming messages."""
    orchestration: GroupChatOrchestration = cl.user_session.get("orchestration")
    runtime = cl.user_session.get("runtime")
    orchestration_result: OrchestrationResult = cl.user_session.get("orchestration_result")
    if not orchestration_result:
        orchestration_result = await orchestration.invoke(
            ChatMessageContent(
                role=AuthorRole.USER,
                content=msg.content,
            ),
            runtime=runtime,
        )
        cl.user_session.set("orchestration_result", orchestration_result)
    else:
        try:
            result = await orchestration_result.get(0.1)
        except TimeoutError:
            await cl.Message(
                content="The task is still in progress. Please wait for the agents to finish.",
            ).send()
            return

        await cl.Message(
            content=f"Task already completed with result: {result}",
        ).send()


if __name__ == "__main__":
    from chainlit.cli import run_chainlit

    run_chainlit(__file__)
