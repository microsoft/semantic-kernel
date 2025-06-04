# Copyright (c) Microsoft. All rights reserved.

import logging
import sys

if sys.version < "3.11":
    from typing_extensions import Self  # pragma: no cover
else:
    from typing import Self  # type: ignore # pragma: no cover
if sys.version < "3.12":
    from typing_extensions import override  # pragma: no cover
else:
    from typing import override  # type: ignore # pragma: no cover

from pydantic import Field

from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.history_reducer.chat_history_reducer import ChatHistoryReducer
from semantic_kernel.contents.history_reducer.chat_history_reducer_utils import (
    SUMMARY_METADATA_KEY,
    contains_function_call_or_result,
    extract_range,
    locate_safe_reduction_index,
    locate_summarization_boundary,
)
from semantic_kernel.exceptions.content_exceptions import ChatHistoryReducerException
from semantic_kernel.utils.feature_stage_decorator import experimental

logger = logging.getLogger(__name__)

DEFAULT_SUMMARIZATION_PROMPT = """
Provide a concise and complete summarization of the entire dialog that does not exceed 5 sentences.

This summary must always:
- Consider both user and assistant interactions
- Maintain continuity for the purpose of further dialog
- Include details from any existing summary
- Focus on the most significant aspects of the dialog

This summary must never:
- Critique, correct, interpret, presume, or assume
- Identify faults, mistakes, misunderstanding, or correctness
- Analyze what has not occurred
- Exclude details from any existing summary
"""


@experimental
class ChatHistorySummarizationReducer(ChatHistoryReducer):
    """A ChatHistory with logic to summarize older messages past a target count.

    This class inherits from ChatHistoryReducer, which in turn inherits from ChatHistory.
    It can be used anywhere a ChatHistory is expected, while adding summarization capability.

    Args:
        target_count: The target message count.
        threshold_count: The threshold count to avoid orphaning messages.
        auto_reduce: Whether to automatically reduce the chat history, default is False.
        service: The ChatCompletion service to use for summarization.
        summarization_instructions: The summarization instructions, optional.
        use_single_summary: Whether to use a single summary message, default is True.
        fail_on_error: Raise error if summarization fails, default is True.
        include_function_content_in_summary: Whether to include function calls/results in the summary, default is False.
        execution_settings: The execution settings for the summarization prompt, optional.

    """

    service: ChatCompletionClientBase
    summarization_instructions: str = Field(
        default=DEFAULT_SUMMARIZATION_PROMPT,
        description="The summarization instructions.",
        kw_only=True,
    )
    use_single_summary: bool = Field(default=True, description="Whether to use a single summary message.")
    fail_on_error: bool = Field(default=True, description="Raise error if summarization fails.")
    include_function_content_in_summary: bool = Field(
        default=False, description="Whether to include function calls/results in the summary."
    )
    execution_settings: PromptExecutionSettings | None = None

    @override
    async def reduce(self) -> Self | None:
        history = self.messages
        if len(history) <= self.target_count + (self.threshold_count or 0):
            return None  # No summarization needed

        logger.info("Performing chat history summarization check...")

        # 1. Identify where existing summary messages end
        insertion_point = locate_summarization_boundary(history)
        if insertion_point == len(history):
            # fallback fix: force boundary to something reasonable
            logger.warning("All messages are summaries, forcing boundary to 0.")
            insertion_point = 0

        # 2. Locate the safe reduction index
        truncation_index = locate_safe_reduction_index(
            history,
            self.target_count,
            self.threshold_count,
            offset_count=insertion_point,
        )
        if truncation_index is None:
            logger.info("No valid truncation index found.")
            return None

        # 3. Extract only the chunk of messages that need summarizing
        #    If include_function_content_in_summary=False, skip function calls/results
        #    Otherwise, keep them but never split pairs.
        messages_to_summarize = extract_range(
            history,
            start=0 if self.use_single_summary else insertion_point,
            end=truncation_index,
            filter_func=(contains_function_call_or_result if not self.include_function_content_in_summary else None),
            preserve_pairs=self.include_function_content_in_summary,
        )

        if not messages_to_summarize:
            logger.info("No messages to summarize.")
            return None

        try:
            # 4. Summarize the extracted messages
            summary_msg = await self._summarize(messages_to_summarize)
            logger.info("Chat History Summarization completed.")
            if not summary_msg:
                return None

            # Mark the newly-created summary with metadata
            summary_msg.metadata[SUMMARY_METADATA_KEY] = True

            # 5. Reassemble the new history
            keep_existing_summaries = []
            if insertion_point > 0 and not self.use_single_summary:
                keep_existing_summaries = history[:insertion_point]

            remainder = history[truncation_index:]
            new_history = [*keep_existing_summaries, summary_msg, *remainder]
            self.messages = new_history

            return self

        except Exception as ex:
            logger.warning("Summarization failed, continuing without summary.")
            if self.fail_on_error:
                raise ChatHistoryReducerException("Chat History Summarization failed.") from ex
            return None

    async def _summarize(self, messages: list[ChatMessageContent]) -> ChatMessageContent | None:
        """Use the ChatCompletion service to generate a single summary message."""
        from semantic_kernel.contents.utils.author_role import AuthorRole

        chat_history = ChatHistory(messages=messages)
        execution_settings = self.execution_settings or self.service.get_prompt_execution_settings_from_settings(
            PromptExecutionSettings()
        )
        chat_history.add_message(
            ChatMessageContent(
                role=getattr(execution_settings, "instruction_role", AuthorRole.SYSTEM),
                content=self.summarization_instructions,
            )
        )
        return await self.service.get_chat_message_content(chat_history=chat_history, settings=execution_settings)

    def __eq__(self, other: object) -> bool:
        """Check if two ChatHistorySummarizationReducer objects are equal."""
        if not isinstance(other, ChatHistorySummarizationReducer):
            return False
        return (
            self.threshold_count == other.threshold_count
            and self.target_count == other.target_count
            and self.use_single_summary == other.use_single_summary
            and self.summarization_instructions == other.summarization_instructions
        )

    def __hash__(self) -> int:
        """Hash the object based on its properties."""
        return hash((
            self.__class__.__name__,
            self.threshold_count,
            self.target_count,
            self.summarization_instructions,
            self.use_single_summary,
            self.fail_on_error,
            self.include_function_content_in_summary,
        ))
