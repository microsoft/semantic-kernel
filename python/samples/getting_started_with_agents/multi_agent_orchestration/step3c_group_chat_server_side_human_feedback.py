"""
Step 3c: Group Chat with Server-Side Human Feedback

This sample demonstrates how to implement human feedback in a server-side GroupChat
using the new overridable get_human_response method, which provides access to instance state.

This addresses the issue where human_response_function was passed as a parameter
but didn't have access to the class instance, making it difficult to implement
server-side scenarios that need context like plan_id.
"""

import asyncio
import uuid
from typing import Any

from semantic_kernel.agents import Agent
from semantic_kernel.agents.orchestration import GroupChatOrchestration
from semantic_kernel.agents.orchestration.group_chat import (
    BooleanResult,
    GroupChatManager,
    MessageResult,
    RoundRobinGroupChatManager,
    StringResult,
)
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.contents import AuthorRole, ChatHistory, ChatMessageContent
from semantic_kernel.core_plugins import TextPlugin
from semantic_kernel.kernel import Kernel


# Mock locks for demonstration purposes
class MockLocks:
    """Mock locks for demonstration purposes."""

    def __init__(self):
        self._locks = {}

    async def lock(self, plan_id: str):
        """Lock a plan_id."""
        self._locks[plan_id] = asyncio.Event()
        print(f"Locked plan_id: {plan_id}")

    async def wait(self, plan_id: str, timeout: float = 180) -> str:
        """Wait for a plan_id to be unlocked with a response."""
        if plan_id not in self._locks:
            raise ValueError(f"Plan ID {plan_id} not found")

        try:
            await asyncio.wait_for(self._locks[plan_id].wait(), timeout=timeout)
            # In a real implementation, this would return the actual response
            # For demo purposes, we'll return a mock response
            return f"Mock response for plan {plan_id}"
        except asyncio.TimeoutError:
            return ""


# Global locks instance for demonstration
locks = MockLocks()


def get_agents() -> list[Agent]:
    """Get the agents for the group chat."""
    kernel = Kernel()
    kernel.import_plugin_from_object(TextPlugin(), "text")

    writer = Agent(
        name="Writer",
        description="A creative writer who can generate slogans and marketing content.",
        instructions="You are a creative writer. Generate engaging and memorable slogans.",
        kernel=kernel,
    )

    reviewer = Agent(
        name="Reviewer",
        description="A marketing expert who reviews and provides feedback on content.",
        instructions="You are a marketing expert. Review the content and provide constructive feedback.",
        kernel=kernel,
    )

    return [writer, reviewer]


class ServerSideGroupChatManager(RoundRobinGroupChatManager):
    """Server-side group chat manager that demonstrates using the overridable get_human_response method."""

    def __init__(self, plan_id: str, **kwargs):
        """Initialize the server-side group chat manager.

        Args:
            plan_id (str): The plan ID for this group chat session.
            **kwargs: Additional arguments passed to the parent class.
        """
        super().__init__(**kwargs)
        self.plan_id = plan_id

    async def should_request_user_input(self, chat_history: ChatHistory) -> BooleanResult:
        """Override the default behavior to request user input after the reviewer's message."""
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

    async def get_human_response(self, chat_history: ChatHistory) -> ChatMessageContent:
        """Override the get_human_response method to provide server-side human feedback.

        This method has access to the instance state (self.plan_id) and can implement
        server-side logic like waiting for external requests.

        Args:
            chat_history (ChatHistory): The chat history of the group chat.

        Returns:
            ChatMessageContent: The human response.
        """
        await locks.lock(self.plan_id)
        try:
            text = await locks.wait(self.plan_id, timeout=180)
        except asyncio.TimeoutError:
            text = ""

        return ChatMessageContent(role=AuthorRole.USER, content=text)


def agent_response_callback(message: ChatMessageContent) -> None:
    """Observer function to print the messages from the agents."""
    print(f"**{message.name}**\n{message.content}")


async def main():
    """Main function to run the agents."""
    # Generate a unique plan ID for this session
    plan_id = str(uuid.uuid4())
    print(f"Starting group chat with plan_id: {plan_id}")

    # 1. Create a group chat orchestration with the server-side manager
    agents = get_agents()
    group_chat_orchestration = GroupChatOrchestration(
        members=agents,
        # Use the new ServerSideGroupChatManager with plan_id
        manager=ServerSideGroupChatManager(
            plan_id=plan_id,
            max_rounds=5,
        ),
        agent_response_callback=agent_response_callback,
    )

    # 2. Create a runtime and start it
    runtime = InProcessRuntime()
    runtime.start()

    # 3. Invoke the orchestration with a task and the runtime
    orchestration_result = await group_chat_orchestration.invoke(
        task="Create a slogan for a new electric SUV that is affordable and fun to drive.",
        runtime=runtime,
    )

    # 4. Wait for the results
    value = await orchestration_result.get()
    print(f"***** Result *****\n{value}")

    # 5. Stop the runtime after the invocation is complete
    await runtime.stop_when_idle()


if __name__ == "__main__":
    asyncio.run(main())
