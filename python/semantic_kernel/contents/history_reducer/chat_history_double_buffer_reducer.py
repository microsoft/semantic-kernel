# Copyright (c) Microsoft. All rights reserved.

"""Double-buffered context window management for chat history.

Implements a proactive context compaction strategy inspired by double buffering
(graphics, 1970s), checkpoint + WAL replay (databases, 1980s), and hopping
windows (stream processing). Instead of stop-the-world summarization when the
context window fills, this reducer begins summarizing at a configurable threshold
while the agent continues working, then swaps to the pre-built back buffer
seamlessly.

"""

import asyncio
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

from enum import Enum

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

GENERATION_METADATA_KEY = "__db_generation__"

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


class RenewalPolicy(str, Enum):
    """Policy for handling accumulated compression debt across generations."""

    RECURSE = "recurse"
    """Summarize the accumulated summaries (meta-compression)."""

    DUMP = "dump"
    """Discard all summaries and start fresh."""


@experimental
class ChatHistoryDoubleBufferReducer(ChatHistoryReducer):
    """A ChatHistory with double-buffered context window management.

    Instead of stop-the-world compaction when the context fills, this reducer
    begins checkpoint summarization at a configurable threshold (default 70% of
    target capacity) while the agent continues working. New messages are appended
    to both the active buffer and a pre-built back buffer. When the active buffer
    hits the swap threshold, the back buffer becomes the new active context.

    Summaries accumulate across generations up to a configurable limit before a
    full renewal (recurse or dump) is triggered, amortizing the cost of full
    renewal across many handoffs.

    Args:
        target_count: The target message count (context capacity).
        threshold_count: The threshold count to avoid orphaning messages.
        auto_reduce: Whether to automatically reduce the chat history.
        service: The ChatCompletion service to use for summarization.
        checkpoint_threshold: Fraction of target_count at which to begin
            checkpoint summarization (0.0-1.0). Default 0.7.
        swap_threshold: Fraction of target_count at which to swap buffers
            (0.0-1.0). Default 0.95. Must be greater than checkpoint_threshold.
        max_generations: Maximum number of summary-on-summary layers before
            triggering renewal. None means no limit (renewal disabled).
        renewal_policy: How to handle accumulated compression debt when
            max_generations is reached. Default RECURSE.
        summarization_instructions: The summarization prompt template.
        fail_on_error: Raise error if summarization fails. Default True.
        include_function_content_in_summary: Whether to include function
            calls/results in the summary. Default False.
        execution_settings: Execution settings for the summarization prompt.
    """

    service: ChatCompletionClientBase
    checkpoint_threshold: float = Field(
        default=0.7,
        gt=0.0,
        le=1.0,
        description="Fraction of target_count at which to begin checkpoint summarization.",
    )
    swap_threshold: float = Field(
        default=0.95,
        gt=0.0,
        le=1.0,
        description="Fraction of target_count at which to swap to the back buffer.",
    )
    max_generations: int | None = Field(
        default=None,
        description="Maximum summary-on-summary layers before renewal. "
        "None means no limit (renewal disabled).",
    )
    renewal_policy: RenewalPolicy = Field(
        default=RenewalPolicy.RECURSE,
        description="How to handle compression debt when max_generations is reached.",
    )
    summarization_instructions: str = Field(
        default=DEFAULT_SUMMARIZATION_PROMPT,
        description="The summarization instructions.",
        kw_only=True,
    )
    fail_on_error: bool = Field(default=True, description="Raise error if summarization fails.")
    include_function_content_in_summary: bool = Field(
        default=False, description="Whether to include function calls/results in the summary."
    )
    execution_settings: PromptExecutionSettings | None = None
    checkpoint_timeout: float = Field(
        default=120.0,
        gt=0.0,
        description="Maximum seconds to wait for a background checkpoint before cancelling.",
    )

    # Internal state — not part of the public API
    _back_buffer: list[ChatMessageContent] | None = None
    _checkpoint_task: asyncio.Task | None = None  # type: ignore[type-arg]
    _checkpoint_in_progress: bool = False
    _current_generation: int = 0

    def model_post_init(self, __context: object) -> None:
        """Validate that swap_threshold > checkpoint_threshold."""
        super().model_post_init(__context)
        if self.swap_threshold <= self.checkpoint_threshold:
            msg = (
                f"swap_threshold ({self.swap_threshold}) must be greater than "
                f"checkpoint_threshold ({self.checkpoint_threshold})"
            )
            raise ValueError(msg)

    @override
    async def reduce(self) -> Self | None:
        """Reduce chat history using double-buffered context management.

        Three-phase algorithm:
        1. Checkpoint: At checkpoint_threshold, fire off background summarization
           to seed the back buffer. The agent continues working immediately.
        2. Concurrent: New messages go to both active and back buffers.
        3. Swap: At swap_threshold, swap to back buffer. If the background
           checkpoint isn't done yet, block on it (graceful degradation to
           stop-the-world, same as today's status quo).

        Returns:
            self if reduction happened, None if no change is needed.
        """
        history = self.messages
        total = len(history)
        checkpoint_limit = int(self.target_count * self.checkpoint_threshold)
        swap_limit = int(self.target_count * self.swap_threshold)

        # Reap completed background checkpoint task
        if self._checkpoint_task is not None and self._checkpoint_task.done():
            try:
                self._checkpoint_task.result()
            except Exception as ex:
                logger.warning("Background checkpoint task failed: %s", ex)
            self._checkpoint_task = None

        # Phase 3: Swap — if we've hit the swap threshold
        if total >= swap_limit:
            # If checkpoint is still running in background, block with timeout.
            if self._checkpoint_task is not None and not self._checkpoint_task.done():
                logger.info(
                    "Swap threshold hit while checkpoint still running. "
                    "Blocking on checkpoint (timeout=%.1fs).",
                    self.checkpoint_timeout,
                )
                try:
                    await asyncio.wait_for(self._checkpoint_task, timeout=self.checkpoint_timeout)
                except TimeoutError:
                    logger.warning(
                        "Background checkpoint timed out after %.1fs. Cancelling.",
                        self.checkpoint_timeout,
                    )
                    self._checkpoint_task.cancel()
                except Exception as ex:
                    logger.warning("Background checkpoint failed at swap time: %s", ex)
                finally:
                    self._checkpoint_task = None
            if self._back_buffer is not None:
                return await self._swap_buffers()
            # No back buffer — checkpoint failed or wasn't started.
            # Fall back to stop-the-world: create checkpoint synchronously, then swap.
            logger.info("Swap threshold reached with no back buffer. Falling back to synchronous checkpoint.")
            try:
                await self._create_checkpoint()
            except Exception as ex:
                logger.warning("Synchronous fallback checkpoint also failed: %s", ex)
            if self._back_buffer is not None:
                return await self._swap_buffers()
            # Truly nothing we can do — checkpoint failed twice. Continue with full context.
            logger.warning("All checkpoint attempts failed at swap time. Continuing with full context.")

        # Phase 1: Checkpoint — kick off background summarization
        if total >= checkpoint_limit and self._back_buffer is None and not self._checkpoint_in_progress:
            self._checkpoint_task = asyncio.create_task(self._create_checkpoint())
            # Return immediately — agent keeps working while checkpoint runs
            return self

        # Phase 2: Concurrent — back buffer kept in sync via add_message_async
        return None

    async def add_message_async(
        self,
        message: ChatMessageContent | dict,
        encoding: str | None = None,
        metadata: dict | None = None,
    ) -> None:
        """Add a message to the chat history and the back buffer if it exists.

        This is the key to the concurrent phase: every new message goes to both
        the active buffer and the back buffer, ensuring the back buffer has
        full-fidelity recent messages.
        """
        await super().add_message_async(message, encoding=encoding, metadata=metadata)

        # Concurrent phase: append to back buffer too
        if self._back_buffer is not None:
            if isinstance(message, ChatMessageContent):
                self._back_buffer.append(message)
            else:
                self._back_buffer.append(ChatMessageContent(**message))

    async def _create_checkpoint(self) -> Self | None:
        """Phase 1: Summarize current context and seed the back buffer."""
        self._checkpoint_in_progress = True
        history = self.messages

        try:
            # Check if we need renewal first
            if self.max_generations is not None and self._current_generation >= self.max_generations:
                await self._perform_renewal()
                # Re-capture — renewal may have reassigned self.messages
                history = self.messages

            # Find the summarization boundary (skip existing summaries)
            insertion_point = locate_summarization_boundary(history)
            if insertion_point == len(history):
                logger.warning("All messages are summaries, forcing boundary to 0.")
                insertion_point = 0

            # Find safe reduction index.
            # For the checkpoint, we want to keep roughly half the messages as
            # recent context in the back buffer, summarizing the rest.
            keep_count = len(history) - insertion_point - max(1, (len(history) - insertion_point) // 2)
            if keep_count < 1:
                keep_count = 1
            truncation_index = locate_safe_reduction_index(
                history,
                keep_count,
                self.threshold_count,
                offset_count=insertion_point,
            )

            if truncation_index is None:
                logger.info("No valid truncation index found for checkpoint.")
                self._checkpoint_in_progress = False
                return None

            # Extract messages to summarize
            messages_to_summarize = extract_range(
                history,
                start=insertion_point,
                end=truncation_index,
                filter_func=(contains_function_call_or_result if not self.include_function_content_in_summary else None),
                preserve_pairs=self.include_function_content_in_summary,
            )

            if not messages_to_summarize:
                logger.info("No messages to summarize for checkpoint.")
                self._checkpoint_in_progress = False
                return None

            # Generate summary
            summary_msg = await self._summarize(messages_to_summarize)
            if not summary_msg:
                self._checkpoint_in_progress = False
                return None

            # Tag summary with metadata
            summary_msg.metadata[SUMMARY_METADATA_KEY] = True
            summary_msg.metadata[GENERATION_METADATA_KEY] = self._current_generation + 1

            # Collect existing summaries to carry forward
            existing_summaries = history[:insertion_point] if insertion_point > 0 else []

            # Seed back buffer: summaries + new summary + recent messages
            remainder = history[truncation_index:]
            self._back_buffer = [*existing_summaries, summary_msg, *remainder]
            self._checkpoint_in_progress = False

            logger.info(
                "Checkpoint created at generation %d. Back buffer seeded with %d messages.",
                self._current_generation + 1,
                len(self._back_buffer),
            )
            return self

        except Exception as ex:
            self._checkpoint_in_progress = False
            logger.warning("Checkpoint creation failed: %s", ex)
            if self.fail_on_error:
                raise ChatHistoryReducerException("Double-buffer checkpoint creation failed.") from ex
            return None

    async def _swap_buffers(self) -> Self:
        """Phase 3: Swap the back buffer into the active context."""
        logger.info(
            "Swapping buffers. Active: %d messages -> Back: %d messages. Generation %d -> %d.",
            len(self.messages),
            len(self._back_buffer) if self._back_buffer else 0,
            self._current_generation,
            self._current_generation + 1,
        )

        self.messages = self._back_buffer or []
        self._back_buffer = None
        self._current_generation += 1
        self._checkpoint_in_progress = False

        return self

    async def _perform_renewal(self) -> None:
        """Handle accumulated compression debt when max_generations is reached."""
        logger.info(
            "Max generations (%d) reached. Performing renewal with policy: %s",
            self.max_generations,
            self.renewal_policy.value,
        )

        if self.renewal_policy == RenewalPolicy.DUMP:
            # Drop all summaries, keep only non-summary messages
            self.messages = [
                msg for msg in self.messages
                if not msg.metadata or SUMMARY_METADATA_KEY not in msg.metadata
            ]
            self._current_generation = 0

        elif self.renewal_policy == RenewalPolicy.RECURSE:
            # Summarize the summaries (meta-compression)
            summary_messages = [
                msg for msg in self.messages
                if msg.metadata and SUMMARY_METADATA_KEY in msg.metadata
            ]
            non_summary_messages = [
                msg for msg in self.messages
                if not msg.metadata or SUMMARY_METADATA_KEY not in msg.metadata
            ]

            if summary_messages:
                meta_summary = await self._summarize(summary_messages)
                if meta_summary:
                    meta_summary.metadata[SUMMARY_METADATA_KEY] = True
                    meta_summary.metadata[GENERATION_METADATA_KEY] = 0
                    self.messages = [meta_summary, *non_summary_messages]
                    self._current_generation = 0
                    return

            # Fallback: if meta-summarization fails, just dump
            self.messages = non_summary_messages
            self._current_generation = 0

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

    @property
    def generation(self) -> int:
        """Current generation count (number of buffer swaps completed)."""
        return self._current_generation

    @property
    def has_back_buffer(self) -> bool:
        """Whether a back buffer is currently active (concurrent phase)."""
        return self._back_buffer is not None

    @property
    def back_buffer_size(self) -> int:
        """Number of messages in the back buffer, or 0 if no back buffer."""
        return len(self._back_buffer) if self._back_buffer is not None else 0

    def __eq__(self, other: object) -> bool:
        """Check if two ChatHistoryDoubleBufferReducer objects are equal."""
        if not isinstance(other, ChatHistoryDoubleBufferReducer):
            return False
        return (
            self.target_count == other.target_count
            and self.threshold_count == other.threshold_count
            and self.checkpoint_threshold == other.checkpoint_threshold
            and self.swap_threshold == other.swap_threshold
            and self.max_generations == other.max_generations
            and self.renewal_policy == other.renewal_policy
            and self.summarization_instructions == other.summarization_instructions
        )

    def __hash__(self) -> int:
        """Hash the object based on its properties."""
        return hash((
            self.__class__.__name__,
            self.target_count,
            self.threshold_count,
            self.checkpoint_threshold,
            self.swap_threshold,
            self.max_generations,
            self.renewal_policy,
            self.summarization_instructions,
            self.fail_on_error,
            self.include_function_content_in_summary,
        ))
