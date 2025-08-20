# Copyright (c) Microsoft. All rights reserved.

import asyncio
import sys

from azure.identity.aio import DefaultAzureCredential

from semantic_kernel.agents import (
    AzureAIAgent,
    AzureAIAgentSettings,
    BooleanResult,
    ChatCompletionAgent,
    GroupChatOrchestration,
    MessageResult,
    RoundRobinGroupChatManager,
)
from semantic_kernel.agents.runtime import InProcessRuntime
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion
from semantic_kernel.contents import AuthorRole, ChatHistory, StreamingChatMessageContent

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover


"""
The following sample demonstrates how to create a Azure AI Foundry Agent, 
a chat completion agent and have them participate in a group chat to work towards
the user's requirement.

Note: This sample use the `AgentGroupChat` feature of Semantic Kernel, which is
no longer maintained. For a replacement, consider using the `GroupChatOrchestration`.

Read more about the `GroupChatOrchestration` here:
https://learn.microsoft.com/semantic-kernel/frameworks/agent/agent-orchestration/group-chat?pivots=programming-language-python

Here is a migration guide from `AgentGroupChat` to `GroupChatOrchestration`:
https://learn.microsoft.com/semantic-kernel/support/migration/group-chat-orchestration-migration-guide?pivots=programming-language-python
"""


REVIEWER_NAME = "ArtDirector"
REVIEWER_INSTRUCTIONS = """
You are an art director who has opinions about copywriting born of a love for David Ogilvy.
The goal is to determine if the given copy is acceptable to print.
If so, state that it is approved. Only include the word "approved" if it is so.
If not, provide insight on how to refine suggested copy without example.
"""
REVIEWER_DESCRIPTION = "An art director who has opinions about copywriting born of a love for David Ogilvy."


COPYWRITER_NAME = "CopyWriter"
COPYWRITER_INSTRUCTIONS = """
You are a copywriter with ten years of experience and are known for brevity and a dry humor.
The goal is to refine and decide on the single best copy as an expert in the field.
Only provide a single proposal per response.
You're laser focused on the goal at hand.
Don't waste time with chit chat.
Consider suggestions when refining an idea.
"""
COPYWRITER_DESCRIPTION = "A copywriter with ten years of experience and known for brevity and a dry humor."


class ApprovalRoundRobinGroupChatManager(RoundRobinGroupChatManager):
    @override
    async def should_terminate(self, chat_history: ChatHistory) -> BooleanResult:
        """Check if the group chat should terminate.

        Args:
            chat_history (ChatHistory): The chat history of the group chat.
        """
        result = await super().should_terminate(chat_history)
        if result.result:
            return result

        # Check if the last message from the reviewer contains "approved"
        last_message = chat_history[-1]
        if (
            last_message.role == AuthorRole.ASSISTANT
            and last_message.name == REVIEWER_NAME
            and "approved" in last_message.content.lower()
        ):
            return BooleanResult(result=True, reason="The reviewer approved the content.")

        return BooleanResult(result=False, reason="The group chat is not ready to terminate.")

    @override
    async def filter_results(self, chat_history: ChatHistory) -> MessageResult:
        """Filter the chat history to only include relevant messages."""
        last_writer_message = next(
            (msg for msg in reversed(chat_history) if msg.role == AuthorRole.ASSISTANT and msg.name == COPYWRITER_NAME),
            None,
        )
        if last_writer_message:
            return MessageResult(
                result=last_writer_message,
                reason="Returning the last message from the writer as the result.",
            )
        return MessageResult(
            result=None,
            reason="No relevant message found from the writer.",
        )


# Flag to indicate if a new message is being received
is_new_message = True


def streaming_agent_response_callback(message: StreamingChatMessageContent, is_final: bool) -> None:
    """Observer function to print the messages from the agents.

    Args:
        message (StreamingChatMessageContent): The streaming message content from the agent.
        is_final (bool): Indicates if this is the final part of the message.
    """
    global is_new_message
    if is_new_message:
        print(f"# {message.name}")
        is_new_message = False
    print(message.content, end="", flush=True)
    if is_final:
        print()
        is_new_message = True


async def main():
    async with (
        # 1. Login to Azure and create a Azure AI Project Client
        DefaultAzureCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        # 2. Create agents
        agent_writer = AzureAIAgent(
            client=client,
            definition=await client.agents.create_agent(
                model=AzureAIAgentSettings().model_deployment_name,
                name=COPYWRITER_NAME,
                instructions=COPYWRITER_INSTRUCTIONS,
                description=COPYWRITER_DESCRIPTION,
            ),
        )
        agent_reviewer = ChatCompletionAgent(
            service=AzureChatCompletion(),
            name=REVIEWER_NAME,
            instructions=REVIEWER_INSTRUCTIONS,
            description=REVIEWER_DESCRIPTION,
        )

        try:
            # 3. Create the group chat orchestration
            group_chat_orchestration = GroupChatOrchestration(
                members=[agent_writer, agent_reviewer],
                # max_rounds is odd, so that the writer gets the last round
                manager=ApprovalRoundRobinGroupChatManager(max_rounds=10),
                streaming_agent_response_callback=streaming_agent_response_callback,
            )

            # 4. Start the orchestration
            runtime = InProcessRuntime()
            runtime.start()
            orchestration_result = await group_chat_orchestration.invoke(
                task="a slogan for a new line of electric cars.",
                runtime=runtime,
            )

            value = await orchestration_result.get()
            print(f"***** Result *****\n{value}")
        finally:
            # 5. Delete the agent
            await client.agents.delete_agent(agent_writer.definition.id)
            await runtime.stop_when_idle()


if __name__ == "__main__":
    asyncio.run(main())
