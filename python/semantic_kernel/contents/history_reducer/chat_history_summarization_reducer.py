# Copyright (c) Microsoft. All rights reserved.

import logging
import sys
from typing import Any

if sys.version < "3.11":
    from typing_extensions import Self  # pragma: no cover
else:
    from typing import Self  # type: ignore # pragma: no cover

from pydantic import Field

from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.const import DEFAULT_SERVICE_NAME
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.history_reducer.chat_history_reducer import ChatHistoryReducer
from semantic_kernel.contents.history_reducer.chat_history_reducer_utils import (
    SUMMARY_METADATA_KEY,
    extract_range,
    locate_safe_reduction_index,
    locate_summarization_boundary,
)
from semantic_kernel.exceptions.content_exceptions import ChatHistoryReducerException

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


class ChatHistorySummarizationReducer(ChatHistoryReducer):
    """A ChatHistory with logic to summarize older messages past a target count.

    Because this class inherits from ChatHistoryReducer (which inherits from ChatHistory),
    it can be used anywhere ChatHistory is expected. It also has built-in summarization logic.
    """

    service: ChatCompletionClientBase
    summarization_instructions: str = Field(
        default_factory=lambda: DEFAULT_SUMMARIZATION_PROMPT, description="The summarization instructions."
    )
    use_single_summary: bool = Field(True, description="Whether to use a single summary message.")
    fail_on_error: bool = Field(True, description="Raise error if summarization fails.")
    service_id: str = Field(
        default_factory=lambda: DEFAULT_SERVICE_NAME, description="The ID of the chat completion service."
    )
    include_function_content_in_summary: bool = Field(
        False, description="Whether to include function calls/results in the summary."
    )

    def __init__(
        self,
        service: ChatCompletionClientBase,
        target_count: int,
        service_id: str | None = None,
        threshold_count: int | None = None,
        summarization_instructions: str | None = None,
        use_single_summary: bool | None = None,
        fail_on_error: bool | None = None,
        include_function_content_in_summary: bool | None = None,
        **kwargs: Any,
    ):
        """Initialize the summarization reducer with summarization settings."""
        args: dict[str, Any] = {
            "service": service,
            "target_count": target_count,
        }

        if service_id is not None:
            args["service_id"] = service_id
        if threshold_count is not None:
            args["threshold_count"] = threshold_count
        if summarization_instructions is not None:
            args["summarization_instructions"] = summarization_instructions
        if use_single_summary is not None:
            args["use_single_summary"] = use_single_summary
        if fail_on_error is not None:
            args["fail_on_error"] = fail_on_error
        if include_function_content_in_summary is not None:
            args["include_function_content_in_summary"] = include_function_content_in_summary

        super().__init__(**args, **kwargs)

    async def reduce(self) -> Self | None:
        """Summarize the older messages past the target message count."""
        history = self.messages
        if len(history) <= self.target_count + (self.threshold_count or 0):
            return None  # No summarization needed

        logger.info("Performing chat history summarization check...")

        # 1. Identify where existing summary messages end
        insertion_point = locate_summarization_boundary(history)
        if insertion_point == len(history):
            # fallback fix: force boundary to something reasonable
            # This is an edge case and will only get triggered if all messages are summaries
            logger.warning("All messages are summaries, forcing boundary to 0.")
            # TODO(evmattso): This is a temporary fix, and should be replaced with a more robust solution.
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
        def _contains_function_call_or_result(msg: ChatMessageContent) -> bool:
            return any(isinstance(item, (FunctionCallContent, FunctionResultContent)) for item in msg.items)

        older_range_start = 0 if self.use_single_summary else insertion_point
        older_range_end = truncation_index

        messages_to_summarize = extract_range(
            history,
            older_range_start,
            older_range_end,
            filter_func=_contains_function_call_or_result if not self.include_function_content_in_summary else None,
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

            # Update self.messages
            self.messages = new_history
            return self

        except Exception as ex:
            logger.warning("Summarization failed, continuing without summary.")
            if self.fail_on_error:
                raise ChatHistoryReducerException("Chat History Summarization failed.") from ex
            return None

    async def _summarize(self, messages: list[ChatMessageContent]) -> ChatMessageContent | None:
        """Use the ChatCompletion service to generate a single summary message."""
        chat_history = ChatHistory(messages=messages)
        chat_history.add_system_message(self.summarization_instructions)

        settings = self.service.get_prompt_execution_settings_class()(service_id=self.service_id)
        return await self.service.get_chat_message_content(chat_history=chat_history, settings=settings)

    def __eq__(self, other: object) -> bool:
        """Compare equality based on summarization settings.

        (Inherited ChatHistory messages are not considered here.)
        """
        if not isinstance(other, ChatHistorySummarizationReducer):
            return False
        return (
            self.threshold_count == other.threshold_count
            and self.target_count == other.target_count
            and self.use_single_summary == other.use_single_summary
            and self.summarization_instructions == other.summarization_instructions
        )

    def __hash__(self) -> int:
        """Return a hash code based on summarization settings."""
        return hash((
            self.__class__.__name__,
            self.threshold_count,
            self.target_count,
            self.summarization_instructions,
            self.use_single_summary,
        ))
