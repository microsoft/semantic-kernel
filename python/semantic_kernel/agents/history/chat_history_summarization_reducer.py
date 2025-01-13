# Copyright (c) Microsoft. All rights reserved.

import logging

from semantic_kernel.agents.history.chat_history_reducer import ChatHistoryReducer
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.kernel_pydantic import KernelBaseModel

from .chat_history_truncation_reducer import extract_range, locate_safe_reduction_index

logger = logging.getLogger(__name__)


class ChatHistorySummarizationReducer(KernelBaseModel, ChatHistoryReducer):
    """Reduce the chat history by summarizing older messages past a target message count.

    Summaries are appended as a single message (with metadata as needed).
    """

    service: ChatCompletionClientBase
    target_count: int
    threshold_count: int | None = 0
    summarization_instructions: str = (
        "Provide a concise and complete summarization (no more than 5 sentences). "
        "This summary must maintain continuity and key context from prior messages."
    )
    use_single_summary: bool = True
    fail_on_error: bool = True

    def __init__(
        self,
        service: ChatCompletionClientBase,
        target_count: int,
        threshold_count: int | None = None,
        summarization_instructions: str | None = None,
        use_single_summary: bool | None = None,
        fail_on_error: bool | None = None,
        **data,
    ):
        """Initialize the summarization reducer."""
        super().__init__(
            service=service,
            target_count=target_count,
            threshold_count=threshold_count or 0,
            summarization_instructions=summarization_instructions
            or "Provide a concise summarization of the conversation.",
            use_single_summary=use_single_summary if use_single_summary is not None else True,
            fail_on_error=True if fail_on_error is None else fail_on_error,
            **data,
        )
        if self.target_count <= 0:
            raise ValueError("Target message count must be greater than zero.")
        if self.threshold_count < 0:
            raise ValueError("The threshold_count must be nonnegative.")

    async def reduce(self, history: list[ChatMessageContent]) -> list[ChatMessageContent] | None:
        """Reduce the chat history by summarizing older messages past a target message count."""
        # If the chat is below threshold, skip
        if len(history) <= self.target_count + (self.threshold_count or 0):
            return None

        # Find a safe index so we don't break user->assistant pairs or function calls.
        # Then we'll summarize that older portion, and keep the rest.
        logger.debug("Performing chat history summarization check...")

        insertion_point = locate_summarization_boundary(history)
        # insertion_point is where the existing summary messages (if any) end

        truncation_index = locate_safe_reduction_index(
            history,
            self.target_count,
            self.threshold_count,
        )
        if truncation_index <= 0:
            return None

        # We'll gather the older portion for summarizing
        older_range_start = 0 if self.use_single_summary else insertion_point
        older_range_end = truncation_index

        messages_to_summarize = extract_range(history, older_range_start, older_range_end)
        if not messages_to_summarize:
            return None

        try:
            # Summarize
            summary_msg = await self._summarize_async(messages_to_summarize)
            if not summary_msg:
                # If no summary came back, we can skip
                return None

            # Re-assemble the final history
            if insertion_point > 0 and not self.use_single_summary:
                # Keep the existing summary messages up to insertion_point
                keep_existing_summaries = history[:insertion_point]
            else:
                keep_existing_summaries = []

            # Then add the new summary
            new_summary = summary_msg
            # (Optionally mark metadata on the summary)
            new_summary.metadata["__summary__"] = True

            # Then keep the remainder from truncation_index onward
            remainder = history[truncation_index:]
            return [*keep_existing_summaries, new_summary, *remainder]
        except Exception as ex:
            if self.fail_on_error:
                raise
            logger.warning("Summarization failed, but continuing without summary. Error: %s", ex)
            return None

    async def _summarize_async(self, messages: list[ChatMessageContent]) -> ChatMessageContent | None:
        # Build a prompt or chat that includes the summarization instructions
        # and the older messages. Then call the ChatCompletionClientBase or similar
        # to get a single summary ChatMessageContent back.
        logger.debug("Sending older messages for summarization.")
        from semantic_kernel.contents.chat_history import ChatHistory

        prompt_history = ChatHistory()
        prompt_history.messages.extend(messages)
        # Insert system instructions for summarization
        prompt_history.messages.append(ChatMessageContent(role="system", content=self.summarization_instructions))

        # Use your chat service to create a single summary message
        summary_messages = await self.service.get_chat_message_contents(prompt_history, settings=None)

        if summary_messages:
            # Return the first
            return summary_messages[0]
        return None


def locate_summarization_boundary(history: list[ChatMessageContent]) -> int:
    """Identify where summary messages end and normal messages begin.

    Check for the `__summary__` metadata.
    If there's no summary, returns 0.
    """
    for idx, msg in enumerate(history):
        if not msg.metadata or "__summary__" not in msg.metadata:
            return idx
    return len(history)
