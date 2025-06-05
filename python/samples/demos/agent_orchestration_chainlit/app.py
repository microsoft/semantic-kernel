# Copyright (c) Microsoft. All rights reserved.

import sys

import chainlit as cl

from semantic_kernel.agents import Agent, ChatCompletionAgent, GroupChatOrchestration
from semantic_kernel.agents.orchestration.group_chat import BooleanResult, RoundRobinGroupChatManager
from semantic_kernel.agents.runtime.in_process.in_process_runtime import InProcessRuntime
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import ChatHistory, ChatMessageContent, StreamingChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover


class CustomRoundRobinGroupChatManager(RoundRobinGroupChatManager):
    """Custom round robin group chat manager to enable user input."""

    @override
    async def should_request_user_input(self, chat_history: ChatHistory) -> BooleanResult:
        """Override the default behavior to request user input after the reviewer's message.

        The manager will check if input from human is needed after each agent message.
        """
        if len(chat_history.messages) == 0:
            return BooleanResult(
                result=False,
                reason="No agents have spoken yet.",
            )
        last_message = chat_history.messages[-1]
        if last_message.name == "Reviewer":
            return BooleanResult(
                result=True,
                reason="User input is needed after the reviewer's message.",
            )

        return BooleanResult(
            result=False,
            reason="User input is not needed if the last message is not from the reviewer.",
        )


def get_agents() -> list[Agent]:
    """Return a list of agents that will participate in the group style discussion.

    Feel free to add or remove agents.
    """
    writer = ChatCompletionAgent(
        name="Writer",
        description="A content writer.",
        instructions=(
            "You are an excellent content writer. You create new content and edit contents based on the feedback."
        ),
        service=AzureChatCompletion(),
    )
    reviewer = ChatCompletionAgent(
        name="Reviewer",
        description="A content reviewer.",
        instructions=(
            "You are an excellent content reviewer. You review the content and provide feedback to the writer."
        ),
        service=AzureChatCompletion(),
    )

    # The order of the agents in the list will be the order in which they will be picked by the round robin manager
    return [writer, reviewer]


async def streaming_agent_response_callback(message_chunk: StreamingChatMessageContent, is_final: bool) -> None:
    streaming_handler = cl.user_session.get("streaming_handler")
    if streaming_handler is None:
        streaming_handler = cl.Message("", author=message_chunk.name)
        cl.user_session.set("streaming_handler", streaming_handler)

    if not is_final:
        await streaming_handler.stream_token(message_chunk.content)
    else:
        await streaming_handler.send()
        cl.user_session.set("streaming_handler", None)


async def human_response_function(chat_histoy: ChatHistory) -> ChatMessageContent:
    """Function to get user input."""
    user_input = await cl.AskUserMessage("Please provide your input", author="Group Manager").send()
    return ChatMessageContent(
        role=AuthorRole.USER, content=user_input["output"] if user_input else "No input provided."
    )


def get_orchestration() -> GroupChatOrchestration:
    """Return a GroupChatOrchestration instance with the agents and custom manager."""
    agents = get_agents()
    return GroupChatOrchestration(
        members=agents,
        # max_rounds is odd, so that the writer gets the last round
        manager=CustomRoundRobinGroupChatManager(
            max_rounds=5,
            human_response_function=human_response_function,
        ),
        streaming_agent_response_callback=streaming_agent_response_callback,
    )


@cl.on_message
async def on_message(msg: cl.Message):
    """Handle incoming messages."""
    orchestration = cl.user_session.get("orchestration")
    if orchestration is None:
        orchestration = get_orchestration()

        runtime = InProcessRuntime()
        runtime.start()

        orchestration_result = await orchestration.invoke(
            ChatMessageContent(
                role=AuthorRole.USER,
                content=msg.content,
            ),
            runtime=runtime,
        )

        cl.user_session.set("orchestration", orchestration)
        cl.user_session.set("orchestration_result", orchestration_result)

        result = await orchestration_result.get()
        await cl.Message(f"Orchestration completed with result: {result}").send()
    else:
        actions = [
            cl.Action(
                name="restart",
                label="Start another task",
                icon="mouse-pointer-click",
            )
        ]

        await cl.Message(
            content="The previous task has completed. Please start a new chat before continueing",
            actions=actions,
        ).send()


@cl.action_callback("restart")
async def on_restart_action():
    """Handle the restart action."""
    cl.chat_context.clear()
    cl.user_session.set("orchestration", None)
