# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging

from semantic_kernel.agents import (
    AgentGroupChat,
    ChatCompletionAgent,
    ChatHistorySummarizationReducer,
    ChatHistoryTruncationReducer,
)
from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, OpenAIChatCompletion
from semantic_kernel.contents import AuthorRole, ChatHistory, ChatMessageContent
from semantic_kernel.kernel import Kernel

#####################################################################
# The following sample demonstrates how to create use the           #
# Semantic Kernel Agent Framework Chat History Reducer. The sample  #
# covers two types of reducers: summarization reduction and a       #
# truncation reduction. For this sample, the ChatCompletionAgent    #
# is used.                                                          #
#####################################################################


# Initialize the logger for debugging and information messages
logger = logging.getLogger(__name__)

# Flag to determine whether to use Azure OpenAI services or OpenAI
# Set this to True if using Azure OpenAI (requires appropriate configuration)
use_azure_openai = True


# Helper function to create and configure a Kernel with the desired chat completion service
def _create_kernel_with_chat_completion(service_id: str) -> Kernel:
    """A helper function to create a kernel with a chat completion service."""
    kernel = Kernel()
    if use_azure_openai:
        # Add Azure OpenAI service to the kernel
        kernel.add_service(AzureChatCompletion(service_id=service_id))
    else:
        # Add OpenAI service to the kernel
        kernel.add_service(OpenAIChatCompletion(service_id=service_id))
    return kernel


class HistoryReducerExample:
    """
    Demonstrates how to create a ChatCompletionAgent with a ChatHistoryReducer
    (either truncation or summarization) and how to invoke that agent
    multiple times while applying the history reduction.
    """

    # Agent-specific settings
    TRANSLATOR_NAME = "NumeroTranslator"  # Name of the agent
    TRANSLATOR_INSTRUCTIONS = "Add one to the latest user number and spell it in Spanish without explanation."

    def create_truncating_agent(self, reducer_msg_count: int, reducer_threshold: int) -> ChatCompletionAgent:
        """
        Creates a ChatCompletionAgent with a truncation-based history reducer.

        Parameters:
        - reducer_msg_count: Target number of messages to retain after truncation.
        - reducer_threshold: Threshold number of messages to trigger truncation.

        Returns:
        - A configured ChatCompletionAgent instance with truncation enabled.
        """
        truncation_reducer = ChatHistoryTruncationReducer(
            target_count=reducer_msg_count, threshold_count=reducer_threshold
        )

        agent = ChatCompletionAgent(
            name=self.TRANSLATOR_NAME,
            instructions=self.TRANSLATOR_INSTRUCTIONS,
            kernel=_create_kernel_with_chat_completion("truncate_agent"),
        )
        agent.history_reducer = truncation_reducer
        return agent

    def create_summarizing_agent(self, reducer_msg_count: int, reducer_threshold: int) -> ChatCompletionAgent:
        """
        Creates a ChatCompletionAgent with a summarization-based history reducer.

        Parameters:
        - reducer_msg_count: Target number of messages to retain after summarization.
        - reducer_threshold: Threshold number of messages to trigger summarization.

        Returns:
        - A configured ChatCompletionAgent instance with summarization enabled.
        """
        kernel = _create_kernel_with_chat_completion("summarize_agent")

        summarization_reducer = ChatHistorySummarizationReducer(
            service=kernel.get_service(service_id="summarize_agent"),
            target_count=reducer_msg_count,
            threshold_count=reducer_threshold,
            summarization_instructions=("Add one to user number, but in Spanish. Then summarize context."),
        )

        agent = ChatCompletionAgent(
            name=self.TRANSLATOR_NAME,
            instructions=self.TRANSLATOR_INSTRUCTIONS,
            kernel=kernel,
        )
        agent.history_reducer = summarization_reducer
        return agent

    async def invoke_agent(self, agent: ChatCompletionAgent, message_count: int):
        """
        Demonstrates agent invocation with direct history management and reduction.

        Parameters:
        - agent: The ChatCompletionAgent to invoke.
        - message_count: The number of messages to simulate in the conversation.
        """
        chat_history = ChatHistory()  # Initialize a new chat history

        index = 1
        while index <= message_count:
            # Provide user input
            user_message = ChatMessageContent(role=AuthorRole.USER, content=str(index))
            chat_history.messages.append(user_message)
            print(f"# User: '{index}'")

            # Attempt history reduction if a reducer is present
            is_reduced = False
            if agent.history_reducer is not None:
                reduced = await agent.history_reducer.reduce(chat_history.messages)
                if reduced is not None:
                    chat_history.messages.clear()
                    chat_history.messages.extend(reduced)
                    is_reduced = True
                    print("@ (History was reduced!)")

            # Invoke the agent and display its response
            async for response in agent.invoke(chat_history):
                chat_history.messages.append(response)
                print(f"# {response.role} - {response.name}: '{response.content}'")

            index += 2
            print(f"@ Message Count: {len(chat_history.messages)}\n")

            # If history was reduced, print summaries
            if is_reduced:
                self._print_summaries_from_front(chat_history.messages)

    async def invoke_chat(self, agent: ChatCompletionAgent, message_count: int):
        """
        Demonstrates agent invocation within a group chat.

        Parameters:
        - agent: The ChatCompletionAgent to invoke.
        - message_count: The number of messages to simulate in the conversation.
        """
        chat = AgentGroupChat()  # Initialize a new group chat
        last_history_count = 0

        index = 1
        while index <= message_count:
            # Add user message to the chat
            user_msg = ChatMessageContent(role=AuthorRole.USER, content=str(index))
            await chat.add_chat_message(user_msg)
            print(f"# User: '{index}'")

            # Invoke the agent and display its response
            async for message in chat.invoke(agent):
                print(f"# {message.role} - {message.name or '*'}: '{message.content}'")

            index += 2

            # Retrieve chat messages in descending order (newest first)
            msgs = []
            async for m in chat.get_chat_messages(agent):
                msgs.append(m)

            print(f"@ Message Count: {len(msgs)}\n")

            # Check for reduction in message count and print summaries
            if len(msgs) < last_history_count:
                self._print_summaries_from_back(msgs)

            last_history_count = len(msgs)

    def _print_summaries_from_front(self, messages: list[ChatMessageContent]):
        """
        Prints summaries from the front of the message list.

        Parameters:
        - messages: List of chat messages to process.
        """
        summary_index = 0
        while summary_index < len(messages):
            msg = messages[summary_index]
            if msg.metadata and msg.metadata.get("__summary__"):
                print(f"\tSummary: {msg.content}")
                summary_index += 1
            else:
                break

    def _print_summaries_from_back(self, messages: list[ChatMessageContent]):
        """
        Prints summaries from the back of the message list.

        Parameters:
        - messages: List of chat messages to process.
        """
        summary_index = len(messages) - 1
        while summary_index >= 0:
            msg = messages[summary_index]
            if msg.metadata and msg.metadata.get("__summary__"):
                print(f"\tSummary: {msg.content}")
                summary_index -= 1
            else:
                break


# Main entry point for the script
async def main():
    # Initialize the example class
    example = HistoryReducerExample()

    # Demonstrate truncation-based reduction
    trunc_agent = example.create_truncating_agent(
        # reducer_msg_count:
        # Purpose: Defines the target number of messages to retain after applying truncation or summarization.
        # What it controls: This parameter determines how much of the most recent conversation history
        #                   is preserved while discarding or summarizing older messages.
        # Why change it?:
        # - Smaller values: Use when memory constraints are tight, or the assistant only needs a brief history
        #   to maintain context.
        # - Larger values: Use when retaining more conversational context is critical for accurate responses
        #   or maintaining a richer dialogue.
        reducer_msg_count=10,
        # reducer_threshold:
        # Purpose: Acts as a buffer to avoid reducing history prematurely when the current message count exceeds
        #          reducer_msg_count by a small margin.
        # What it controls: Helps ensure that essential paired messages (like a user query and the assistant’s response)
        #                   are not "orphaned" or lost during truncation or summarization.
        # Why change it?:
        # - Smaller values: Use when you want stricter reduction criteria and are okay with possibly cutting older
        #   pairs of messages sooner.
        # - Larger values: Use when you want to minimize the risk of cutting a critical part of the conversation,
        #   especially for sensitive interactions like API function calls or complex responses.
        reducer_threshold=10,
    )
    print("===TruncatedAgentReduction Demo===")
    await example.invoke_agent(trunc_agent, message_count=50)

    # Demonstrate summarization-based reduction
    sum_agent = example.create_summarizing_agent(
        # Same configuration for summarization-based reduction
        reducer_msg_count=10,  # Target number of messages to retain
        reducer_threshold=10,  # Buffer to avoid premature reduction
    )
    print("\n===SummarizedAgentReduction Demo===")
    await example.invoke_agent(sum_agent, message_count=50)

    # Demonstrate group chat with truncation
    print("\n===TruncatedChatReduction Demo===")
    await example.invoke_chat(trunc_agent, message_count=50)

    # Demonstrate group chat with summarization
    print("\n===SummarizedChatReduction Demo===")
    await example.invoke_chat(sum_agent, message_count=50)


# Interaction between reducer_msg_count and reducer_threshold:
# The combination of these values determines when reduction occurs and how much history is kept.
# Example:
# If reducer_msg_count = 10 and reducer_threshold = 5, history will not be truncated until the total message count
# exceeds 15. This approach ensures flexibility in retaining conversational context while still adhering to memory
# constraints.

# Recommendations:
# - Adjust for performance: Use a lower reducer_msg_count in environments with limited memory or when the assistant
#   needs faster processing times.
# - Context sensitivity: Increase reducer_msg_count and reducer_threshold in use cases where maintaining continuity
#   across multiple interactions is essential (e.g., multi-turn conversations or complex workflows).
# - Experiment: Start with the default values (10 and 10) and refine based on your application's behavior and the
#   assistant's response quality.


# Execute the main function if the script is run directly
if __name__ == "__main__":
    asyncio.run(main())
