# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import Any

from pydantic import Field

from semantic_kernel.agents.history.chat_history_reducer import ChatHistoryReducer
from semantic_kernel.agents.history.chat_history_reducer_extensions import (
    SUMMARY_METADATA_KEY,
    extract_range,
    locate_safe_reduction_index,
    locate_summarization_boundary,
)
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.const import DEFAULT_SERVICE_NAME
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions.agent_exceptions import AgentChatHistoryReducerException
from semantic_kernel.kernel_pydantic import KernelBaseModel

logger = logging.getLogger(__name__)

DEFAULT_SUMMARIZATION_INSTRUCTIONS = """
        Provide a concise and complete summarization of the entire dialog that does not exceed 5 sentences

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


class ChatHistorySummarizationReducer(KernelBaseModel, ChatHistoryReducer):
    """Reduce the chat history by summarizing older messages past a target message count."""

    service: ChatCompletionClientBase
    target_count: int = Field(..., gt=0, description="The target message count to reduce the chat history to.")
    threshold_count: int = Field(
        default_factory=lambda: 0, ge=0, description="The threshold count to avoid orphaning messages."
    )
    summarization_instructions: str = Field(
        default_factory=lambda: DEFAULT_SUMMARIZATION_INSTRUCTIONS, description="The summarization instructions."
    )
    use_single_summary: bool = Field(default=True, description="Whether to use a single summary message.")
    fail_on_error: bool = Field(default=True, description="Whether to raise an error if summarization fails.")
    service_id: str = Field(
        default_factory=lambda: DEFAULT_SERVICE_NAME, description="The service id for the chat completion service."
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
    ):
        """Initialize the summarization reducer."""
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

        super().__init__(**args)

    def __eq__(self, other: object) -> bool:
        """Return whether this instance is equal to another."""
        if not isinstance(other, ChatHistorySummarizationReducer):
            return False
        return (
            self.threshold_count == other.threshold_count
            and self.target_count == other.target_count
            and self.use_single_summary == other.use_single_summary
            and self.summarization_instructions == other.summarization_instructions
        )

    def __hash__(self) -> int:
        """Return a hash code for this instance."""
        return hash((
            self.__class__.__name__,
            self.threshold_count,
            self.target_count,
            self.summarization_instructions,
            self.use_single_summary,
        ))

    async def reduce(self, history: list[ChatMessageContent]) -> list[ChatMessageContent] | None:
        """Summarize the older messages past the target message count."""
        if len(history) <= self.target_count + (self.threshold_count or 0):
            return None

        logger.info("Performing chat history summarization check...")

        insertion_point = locate_summarization_boundary(history)
        truncation_index = locate_safe_reduction_index(
            history,
            self.target_count,
            self.threshold_count,
            offset_count=insertion_point,
        )
        if truncation_index < 0:
            logger.info(
                f"No truncation index found. Target count: {self.target_count}, Threshold count: {self.threshold_count}"
            )
            return None

        older_range_start = 0 if self.use_single_summary else insertion_point
        older_range_end = truncation_index
        messages_to_summarize = extract_range(history, older_range_start, older_range_end)
        if not messages_to_summarize:
            logger.info("No messages to summarize.")
            return None

        try:
            summary_msg = await self._summarize(messages_to_summarize)
            logger.info("Summarization completed.")
            if not summary_msg:
                return None
            summary_msg.metadata[SUMMARY_METADATA_KEY] = True

            keep_existing_summaries = []
            if insertion_point > 0 and not self.use_single_summary:
                keep_existing_summaries = history[:insertion_point]

            remainder = history[truncation_index:]
            return [*keep_existing_summaries, summary_msg, *remainder]

        except Exception as ex:
            logger.warning("Summarization failed, but continuing without summary.")
            if self.fail_on_error:
                raise AgentChatHistoryReducerException("Chat History Summarization failed.") from ex
            return None

    async def _summarize(self, messages: list[ChatMessageContent]) -> ChatMessageContent | None:
        """Use the ChatCompletion service to generate a single summary message."""
        from semantic_kernel.contents.chat_history import ChatHistory

        chat_history = ChatHistory()
        chat_history.messages.extend(messages)
        chat_history.messages.append(
            ChatMessageContent(role=AuthorRole.SYSTEM, content=self.summarization_instructions)
        )

        settings = self.service.get_prompt_execution_settings_class()(service_id=self.service_id)
        summary_messages = await self.service.get_chat_message_contents(chat_history=chat_history, settings=settings)
        return summary_messages[0] if summary_messages else None
