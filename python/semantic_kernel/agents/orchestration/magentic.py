# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
import sys
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable
from typing import Annotated

from pydantic import Field

from semantic_kernel.agents.agent import Agent
from semantic_kernel.agents.orchestration.agent_actor_base import ActorBase, AgentActorBase
from semantic_kernel.agents.orchestration.orchestration_base import DefaultTypeAlias, OrchestrationBase, TIn, TOut
from semantic_kernel.agents.orchestration.prompts._magentic_prompts import (
    ORCHESTRATOR_FINAL_ANSWER_PROMPT,
    ORCHESTRATOR_PROGRESS_LEDGER_PROMPT,
    ORCHESTRATOR_TASK_LEDGER_FACTS_PROMPT,
    ORCHESTRATOR_TASK_LEDGER_FACTS_UPDATE_PROMPT,
    ORCHESTRATOR_TASK_LEDGER_FULL_PROMPT,
    ORCHESTRATOR_TASK_LEDGER_PLAN_PROMPT,
    ORCHESTRATOR_TASK_LEDGER_PLAN_UPDATE_PROMPT,
)
from semantic_kernel.agents.runtime.core.cancellation_token import CancellationToken
from semantic_kernel.agents.runtime.core.core_runtime import CoreRuntime
from semantic_kernel.agents.runtime.core.message_context import MessageContext
from semantic_kernel.agents.runtime.core.routed_agent import message_handler
from semantic_kernel.agents.runtime.core.topic import TopicId
from semantic_kernel.agents.runtime.in_process.type_subscription import TypeSubscription
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel import Kernel
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.prompt_template.kernel_prompt_template import KernelPromptTemplate
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig
from semantic_kernel.utils.feature_stage_decorator import experimental

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

logger: logging.Logger = logging.getLogger(__name__)


# region Messages and Types


@experimental
class MagenticStartMessage(KernelBaseModel):
    """A message to start a magentic group chat."""

    body: ChatMessageContent


@experimental
class MagenticRequestMessage(KernelBaseModel):
    """A request message type for agents in a magentic group chat."""

    agent_name: str


@experimental
class MagenticResponseMessage(KernelBaseModel):
    """A response message type from agents in a magentic group chat."""

    body: ChatMessageContent


@experimental
class MagenticResetMessage(KernelBaseModel):
    """A message to reset a participant's chat history in a magentic group chat."""

    pass


@experimental
class ProgressLedgerItem(KernelBaseModel):
    """A progress ledger item."""

    reason: str
    answer: str | bool


@experimental
class ProgressLedger(KernelBaseModel):
    """A progress ledger."""

    is_request_satisfied: ProgressLedgerItem
    is_in_loop: ProgressLedgerItem
    is_progress_being_made: ProgressLedgerItem
    next_speaker: ProgressLedgerItem
    instruction_or_question: ProgressLedgerItem


@experimental
class MagenticContext(KernelBaseModel):
    """Context for the Magentic manager."""

    task: Annotated[ChatMessageContent, Field(description="The task to be completed.")]
    chat_history: Annotated[
        ChatHistory, Field(description="The chat history to be used to generate the facts and plan.")
    ] = ChatHistory()
    participant_descriptions: Annotated[
        dict[str, str], Field(description="The descriptions of the participants in the group.")
    ]
    round_count: Annotated[int, Field(description="The number of rounds completed.")] = 0
    stall_count: Annotated[int, Field(description="The number of stalls detected.")] = 0
    reset_count: Annotated[int, Field(description="The number of resets detected.")] = 0

    def reset(self) -> None:
        """Reset the context.

        This will clear the chat history and reset the stall count.
        This won't reset the task, round count, or participant descriptions.
        """
        self.chat_history.clear()
        self.stall_count = 0
        self.reset_count += 1


# endregion Messages and Types

# region MagenticManager


@experimental
class MagenticManagerBase(KernelBaseModel, ABC):
    """Base class for the Magentic One manager."""

    max_stall_count: Annotated[int, Field(description="The maximum number of stalls allowed before a reset.", ge=0)] = 3
    max_reset_count: Annotated[int | None, Field(description="The maximum number of resets allowed.", ge=0)] = None
    max_round_count: Annotated[
        int | None, Field(description="The maximum number of rounds (agent responses) allowed.", gt=0)
    ] = None

    @abstractmethod
    async def plan(self, magentic_context: MagenticContext) -> ChatMessageContent:
        """Create a plan for the task.

        This is called when the task is first started.

        Args:
            magentic_context (MagenticContext): The context for the Magentic manager.

        Returns:
            ChatMessageContent: The task ledger.
        """
        ...

    @abstractmethod
    async def replan(self, magentic_context: MagenticContext) -> ChatMessageContent:
        """Replan for the task.

        This is called when the task is stalled or looping.

        Args:
            magentic_context (MagenticContext): The context for the Magentic manager.

        Returns:
            ChatMessageContent: The updated task ledger.
        """
        ...

    @abstractmethod
    async def create_progress_ledger(self, magentic_context: MagenticContext) -> ProgressLedger:
        """Create a progress ledger.

        Args:
            magentic_context (MagenticContext): The context for the Magentic manager.

        Returns:
            ProgressLedger: The progress ledger.
        """
        ...

    @abstractmethod
    async def prepare_final_answer(self, magentic_context: MagenticContext) -> ChatMessageContent:
        """Prepare the final answer.

        Args:
            magentic_context (MagenticContext): The context for the Magentic manager.

        Returns:
            ChatMessageContent: The final answer.
        """
        ...


@experimental
class _TaskLedger(KernelBaseModel):
    """Task ledger for the Standard Magentic manager."""

    facts: Annotated[ChatMessageContent, Field(description="The facts about the task.")]
    plan: Annotated[ChatMessageContent, Field(description="The plan for the task.")]


@experimental
class StandardMagenticManager(MagenticManagerBase):
    """Standard Magentic manager implementation.

    This is the default implementation of the Magentic manager.
    It uses the task ledger to keep track of the facts and plan for the task.

    This implementation requires a chat completion model with structured outputs.
    """

    chat_completion_service: ChatCompletionClientBase
    prompt_execution_settings: PromptExecutionSettings

    task_ledger_facts_prompt: str = ORCHESTRATOR_TASK_LEDGER_FACTS_PROMPT
    task_ledger_plan_prompt: str = ORCHESTRATOR_TASK_LEDGER_PLAN_PROMPT
    task_ledger_full_prompt: str = ORCHESTRATOR_TASK_LEDGER_FULL_PROMPT
    task_ledger_facts_update_prompt: str = ORCHESTRATOR_TASK_LEDGER_FACTS_UPDATE_PROMPT
    task_ledger_plan_update_prompt: str = ORCHESTRATOR_TASK_LEDGER_PLAN_UPDATE_PROMPT
    progress_ledger_prompt: str = ORCHESTRATOR_PROGRESS_LEDGER_PROMPT
    final_answer_prompt: str = ORCHESTRATOR_FINAL_ANSWER_PROMPT

    task_ledger: _TaskLedger | None = None

    def __init__(
        self,
        chat_completion_service: ChatCompletionClientBase,
        prompt_execution_settings: PromptExecutionSettings | None = None,
        **kwargs,
    ) -> None:
        """Initialize the Standard Magentic manager.

        Args:
            chat_completion_service (ChatCompletionClientBase): The chat completion service to use.
            prompt_execution_settings (PromptExecutionSettings | None): The prompt execution settings to use.
            **kwargs: Additional keyword arguments for prompts:
                - task_ledger_facts_prompt: The prompt to use for the task ledger facts.
                - task_ledger_plan_prompt: The prompt to use for the task ledger plan.
                - task_ledger_full_prompt: The prompt to use for the full task ledger.
                - task_ledger_facts_update_prompt: The prompt to use for the task ledger facts update.
                - task_ledger_plan_update_prompt: The prompt to use for the task ledger plan update.
                - progress_ledger_prompt: The prompt to use for the progress ledger.
                - final_answer_prompt: The prompt to use for the final answer.
        """
        # Bast effort to make sure the service supports structured output. Even if the service supports
        # structured output, the model may not support it, in which case there is no good way to check.
        if prompt_execution_settings is None:
            prompt_execution_settings = chat_completion_service.instantiate_prompt_execution_settings()
            if not hasattr(prompt_execution_settings, "response_format"):
                raise ValueError("The service must support structured output.")
        else:
            if not hasattr(prompt_execution_settings, "response_format"):
                raise ValueError("The service must support structured output.")
            if getattr(prompt_execution_settings, "response_format", None) is not None:
                raise ValueError("The prompt execution settings must not have a response format set.")

        super().__init__(
            chat_completion_service=chat_completion_service,
            prompt_execution_settings=prompt_execution_settings,
            **kwargs,
        )

    @override
    async def plan(self, magentic_context: MagenticContext) -> ChatMessageContent:
        """Plan the task.

        Args:
            magentic_context (MagenticContext): The context for the Magentic manager.

        Returns:
            ChatMessageContent: The task ledger.
        """
        # 1. Gather the facts
        prompt_template = KernelPromptTemplate(
            prompt_template_config=PromptTemplateConfig(template=self.task_ledger_facts_prompt)
        )
        magentic_context.chat_history.add_message(
            ChatMessageContent(
                role=AuthorRole.USER,
                content=await prompt_template.render(Kernel(), KernelArguments(task=magentic_context.task.content)),
            )
        )
        facts = await self.chat_completion_service.get_chat_message_content(
            magentic_context.chat_history,
            self.prompt_execution_settings,
        )
        assert facts is not None  # nosec B101
        magentic_context.chat_history.add_message(facts)

        # 2. Create the plan
        prompt_template = KernelPromptTemplate(
            prompt_template_config=PromptTemplateConfig(template=self.task_ledger_plan_prompt)
        )
        magentic_context.chat_history.add_message(
            ChatMessageContent(
                role=AuthorRole.USER,
                content=await prompt_template.render(
                    Kernel(),
                    KernelArguments(team=magentic_context.participant_descriptions),
                ),
            )
        )
        plan = await self.chat_completion_service.get_chat_message_content(
            magentic_context.chat_history,
            self.prompt_execution_settings,
        )
        assert plan is not None  # nosec B101

        self.task_ledger = _TaskLedger(facts=facts, plan=plan)
        return await self._render_task_ledger(magentic_context)

    @override
    async def replan(self, magentic_context: MagenticContext) -> ChatMessageContent:
        """Replan the task.

        Args:
            magentic_context (MagenticContext): The context for the Magentic manager.

        Returns:
            ChatMessageContent: The updated task ledger.
        """
        if self.task_ledger is None:
            raise RuntimeError("The task ledger is not initialized. Planning needs to happen first.")

        # 1. Update the facts
        prompt_template = KernelPromptTemplate(
            prompt_template_config=PromptTemplateConfig(template=self.task_ledger_facts_update_prompt)
        )
        magentic_context.chat_history.add_message(
            ChatMessageContent(
                role=AuthorRole.USER,
                content=await prompt_template.render(
                    Kernel(),
                    KernelArguments(task=magentic_context.task.content, old_facts=self.task_ledger.facts.content),
                ),
            )
        )
        facts = await self.chat_completion_service.get_chat_message_content(
            magentic_context.chat_history,
            self.prompt_execution_settings,
        )
        assert facts is not None  # nosec B101
        magentic_context.chat_history.add_message(facts)

        # 2. Update the plan
        prompt_template = KernelPromptTemplate(
            prompt_template_config=PromptTemplateConfig(template=self.task_ledger_plan_update_prompt)
        )
        magentic_context.chat_history.add_message(
            ChatMessageContent(
                role=AuthorRole.USER,
                content=await prompt_template.render(
                    Kernel(),
                    KernelArguments(team=magentic_context.participant_descriptions),
                ),
            )
        )
        plan = await self.chat_completion_service.get_chat_message_content(
            magentic_context.chat_history,
            self.prompt_execution_settings,
        )
        assert plan is not None  # nosec B101

        self.task_ledger.facts = facts
        self.task_ledger.plan = plan
        return await self._render_task_ledger(magentic_context)

    async def _render_task_ledger(self, magentic_context: MagenticContext) -> ChatMessageContent:
        """Render the task ledger to a string.

        Args:
            magentic_context (MagenticContext): The context for the Magentic manager.

        Returns:
            ChatMessageContent: The rendered task ledger.
        """
        if self.task_ledger is None:
            raise RuntimeError("The task ledger is not initialized. Planning needs to happen first.")

        prompt_template = KernelPromptTemplate(
            prompt_template_config=PromptTemplateConfig(template=self.task_ledger_full_prompt)
        )

        rendered_task_ledger = await prompt_template.render(
            Kernel(),
            KernelArguments(
                task=magentic_context.task.content,
                team=magentic_context.participant_descriptions,
                facts=self.task_ledger.facts.content,
                plan=self.task_ledger.plan.content,
            ),
        )

        return ChatMessageContent(role=AuthorRole.ASSISTANT, content=rendered_task_ledger)

    @override
    async def create_progress_ledger(self, magentic_context: MagenticContext) -> ProgressLedger:
        """Create a progress ledger.

        Args:
            magentic_context (MagenticContext): The context for the Magentic manager.

        Returns:
            ProgressLedger: The progress ledger.
        """
        prompt_template = KernelPromptTemplate(
            prompt_template_config=PromptTemplateConfig(template=self.progress_ledger_prompt)
        )
        progress_ledger_prompt = await prompt_template.render(
            Kernel(),
            KernelArguments(
                task=magentic_context.task.content,
                team=magentic_context.participant_descriptions,
                names=", ".join(magentic_context.participant_descriptions.keys()),
            ),
        )
        magentic_context.chat_history.add_message(
            ChatMessageContent(role=AuthorRole.USER, content=progress_ledger_prompt)
        )

        prompt_execution_settings_clone = PromptExecutionSettings.from_prompt_execution_settings(
            self.prompt_execution_settings
        )
        prompt_execution_settings_clone.update_from_prompt_execution_settings(
            PromptExecutionSettings(extension_data={"response_format": ProgressLedger})
        )

        response = await self.chat_completion_service.get_chat_message_content(
            magentic_context.chat_history,
            prompt_execution_settings_clone,
        )
        assert response is not None  # nosec B101

        return ProgressLedger.model_validate_json(response.content)

    @override
    async def prepare_final_answer(self, magentic_context: MagenticContext) -> ChatMessageContent:
        """Prepare the final answer.

        Args:
            magentic_context (MagenticContext): The context for the Magentic manager.

        Returns:
            ChatMessageContent: The final answer.
        """
        prompt_template = KernelPromptTemplate(
            prompt_template_config=PromptTemplateConfig(template=self.final_answer_prompt)
        )
        magentic_context.chat_history.add_message(
            ChatMessageContent(
                role=AuthorRole.USER,
                content=await prompt_template.render(Kernel(), KernelArguments(task=magentic_context.task)),
            )
        )

        response = await self.chat_completion_service.get_chat_message_content(
            magentic_context.chat_history,
            self.prompt_execution_settings,
        )
        assert response is not None  # nosec B101

        return response


# endregion MagenticManager

# region MagenticManagerActor


@experimental
class MagenticManagerActor(ActorBase):
    """Actor for the Magentic One manager."""

    def __init__(
        self,
        manager: MagenticManagerBase,
        internal_topic_type: str,
        participant_descriptions: dict[str, str],
        result_callback: Callable[[DefaultTypeAlias], Awaitable[None]] | None = None,
    ) -> None:
        """Initialize the Magentic One manager actor.

        Args:
            manager (MagenticManagerBase): The Magentic One manager.
            internal_topic_type (str): The internal topic type.
            participant_descriptions (dict[str, str]): The participant descriptions.
            result_callback (Callable | None): A callback function to handle the final answer.
        """
        self._manager = manager
        self._internal_topic_type = internal_topic_type
        self._result_callback = result_callback
        self._participant_descriptions = participant_descriptions
        self._context: MagenticContext | None = None
        self._task_ledger: ChatMessageContent | None = None

        super().__init__(description="Magentic One Manager")

    @message_handler
    async def _handle_start_message(self, message: MagenticStartMessage, ctx: MessageContext) -> None:
        """Handle the start message for the Magentic One manager."""
        logger.debug(f"{self.id}: Received Magentic One start message.")

        self._context = MagenticContext(
            task=message.body,
            participant_descriptions=self._participant_descriptions,
        )

        # Initial planning
        self._task_ledger = await self._manager.plan(self._context.model_copy(deep=True))

        await self._run_outer_loop(ctx.cancellation_token)

    @message_handler
    async def _handle_response_message(self, message: MagenticResponseMessage, ctx: MessageContext) -> None:
        """Handle the response message for the Magentic One manager."""
        if self._context is None or self._task_ledger is None:
            raise RuntimeError("The Magentic manager is not started yet. Make sure to send a start message first.")

        if message.body.role != AuthorRole.USER:
            self._context.chat_history.add_message(
                ChatMessageContent(
                    role=AuthorRole.USER,
                    content=f"Transferred to {message.body.name}",
                )
            )
        self._context.chat_history.add_message(message.body)

        logger.debug(f"{self.id}: Running inner loop.")
        await self._run_inner_loop(ctx.cancellation_token)

    async def _run_outer_loop(self, cancellation_token: CancellationToken) -> None:
        if self._context is None or self._task_ledger is None:
            raise RuntimeError("The Magentic manager is not started yet. Make sure to send a start message first.")

        # 1. Publish the rendered task ledger to the group chat.
        # Need to add the task ledger to the orchestrator's chat history
        # since the publisher won't receive the message it sends even though
        # the publisher also subscribes to the topic.
        self._context.chat_history.add_message(
            ChatMessageContent(
                role=AuthorRole.ASSISTANT,
                content=self._task_ledger.content,
                name=self.__class__.__name__,
            )
        )

        logger.debug(f"Initial task ledger:\n{self._task_ledger.content}")
        await self.publish_message(
            MagenticResponseMessage(
                body=self._context.chat_history.messages[-1],
            ),
            TopicId(self._internal_topic_type, self.id.key),
            cancellation_token=cancellation_token,
        )

        # 2. Start the inner loop.
        await self._run_inner_loop(cancellation_token)

    async def _run_inner_loop(self, cancellation_token: CancellationToken) -> None:
        if self._context is None or self._task_ledger is None:
            raise RuntimeError("The Magentic manager is not started yet. Make sure to send a start message first.")

        within_limits = await self._check_within_limits()
        if not within_limits:
            return
        self._context.round_count += 1

        # 1. Create a progress ledger
        current_progress_ledger = await self._manager.create_progress_ledger(self._context.model_copy(deep=True))
        logger.debug(f"Current progress ledger:\n{current_progress_ledger.model_dump_json(indent=2)}")

        # 2. Process the progress ledger
        # 2.1 Check for task completion
        if current_progress_ledger.is_request_satisfied.answer:
            logger.debug("Task completed.")
            await self._prepare_final_answer()
            return
        # 2.2 Check for stalling or looping
        if not current_progress_ledger.is_progress_being_made.answer or current_progress_ledger.is_in_loop.answer:
            self._context.stall_count += 1
        else:
            self._context.stall_count = max(0, self._context.stall_count - 1)

        if self._context.stall_count > self._manager.max_stall_count:
            logger.debug("Stalling detected. Resetting the task.")
            self._task_ledger = await self._manager.replan(self._context.model_copy(deep=True))
            await self._reset_for_outer_loop(cancellation_token)
            logger.debug("Restarting outer loop.")
            await self._run_outer_loop(cancellation_token)
            return

        # 2.3 Publish for next step
        next_step = current_progress_ledger.instruction_or_question.answer
        self._context.chat_history.add_message(
            ChatMessageContent(
                role=AuthorRole.ASSISTANT,
                content=next_step if isinstance(next_step, str) else str(next_step),
                name=self.__class__.__name__,
            )
        )
        await self.publish_message(
            MagenticResponseMessage(
                body=self._context.chat_history.messages[-1],
            ),
            TopicId(self._internal_topic_type, self.id.key),
            cancellation_token=cancellation_token,
        )

        # 2.4 Request the next speaker to speak
        next_speaker = current_progress_ledger.next_speaker.answer
        if next_speaker not in self._participant_descriptions:
            raise ValueError(f"Unknown speaker: {next_speaker}")

        logger.debug(f"Magentic One manager selected agent: {next_speaker}")

        await self.publish_message(
            MagenticRequestMessage(agent_name=next_speaker),
            TopicId(self._internal_topic_type, self.id.key),
            cancellation_token=cancellation_token,
        )

    async def _reset_for_outer_loop(self, cancellation_token: CancellationToken) -> None:
        """Reset the context for the outer loop."""
        if self._context is None:
            raise RuntimeError("The Magentic manager is not started yet. Make sure to send a start message first.")

        await self.publish_message(
            MagenticResetMessage(),
            TopicId(self._internal_topic_type, self.id.key),
            cancellation_token=cancellation_token,
        )
        self._context.reset()

    async def _prepare_final_answer(self) -> None:
        """Prepare the final answer and send it to the result callback."""
        if self._context is None:
            raise RuntimeError("The Magentic manager is not started yet. Make sure to send a start message first.")

        final_answer = await self._manager.prepare_final_answer(self._context.model_copy(deep=True))

        if self._result_callback:
            await self._result_callback(final_answer)

    async def _check_within_limits(self) -> bool:
        """Check if the manager is within the limits."""
        if self._context is None:
            raise RuntimeError("The Magentic manager is not started yet. Make sure to send a start message first.")

        if (
            self._manager.max_round_count is not None and self._context.round_count >= self._manager.max_round_count
        ) or (self._manager.max_reset_count is not None and self._context.reset_count > self._manager.max_reset_count):
            message = (
                "Max round count reached."
                if self._manager.max_round_count and self._context.round_count >= self._manager.max_round_count
                else "Max reset count reached."
            )
            logger.debug(message)
            if self._result_callback:
                await self._result_callback(
                    ChatMessageContent(role=AuthorRole.ASSISTANT, content=message, name=self.__class__.__name__)
                )
            return False

        return True


# endregion MagenticManagerActor

# region MagenticAgentActor


@experimental
class MagenticAgentActor(AgentActorBase):
    """An agent actor that process messages in a Magentic One group chat."""

    @message_handler
    async def _handle_response_message(self, message: MagenticResponseMessage, ctx: MessageContext) -> None:
        logger.debug(f"{self.id}: Received response message.")
        if self._agent_thread is not None:
            await self._agent_thread.on_new_message(message.body)
        else:
            self._chat_history.add_message(message.body)

    @message_handler
    async def _handle_request_message(self, message: MagenticRequestMessage, ctx: MessageContext) -> None:
        if message.agent_name != self._agent.name:
            return

        logger.debug(f"{self.id}: Received request message.")

        response = await self._invoke_agent()

        logger.debug(f"{self.id} responded with {response}.")

        await self.publish_message(
            MagenticResponseMessage(body=response),
            TopicId(self._internal_topic_type, self.id.key),
            cancellation_token=ctx.cancellation_token,
        )

    @message_handler
    async def _handle_reset_message(self, message: MagenticResetMessage, ctx: MessageContext) -> None:
        """Handle the reset message for the Magentic One group chat."""
        logger.debug(f"{self.id}: Received reset message.")
        self._chat_history.clear()
        if self._agent_thread:
            await self._agent_thread.delete()
            self._agent_thread = None


# endregion MagenticAgentActor

# region MagenticOrchestration


@experimental
class MagenticOrchestration(OrchestrationBase[TIn, TOut]):
    """The Magentic One pattern orchestration."""

    def __init__(
        self,
        members: list[Agent],
        manager: MagenticManagerBase,
        name: str | None = None,
        description: str | None = None,
        input_transform: Callable[[TIn], Awaitable[DefaultTypeAlias] | DefaultTypeAlias] | None = None,
        output_transform: Callable[[DefaultTypeAlias], Awaitable[TOut] | TOut] | None = None,
        agent_response_callback: Callable[[DefaultTypeAlias], Awaitable[None] | None] | None = None,
        streaming_agent_response_callback: Callable[[StreamingChatMessageContent, bool], Awaitable[None] | None]
        | None = None,
    ) -> None:
        """Initialize the Magentic One orchestration.

        Args:
            members (list[Agent]): A list of agents.
            manager (MagenticManagerBase): The manager for the Magentic One pattern.
            name (str | None): The name of the orchestration.
            description (str | None): The description of the orchestration.
            input_transform (Callable | None): A function that transforms the external input message.
            output_transform (Callable | None): A function that transforms the internal output message.
            agent_response_callback (Callable | None): A function that is called when a response is produced
                by the agents.
            streaming_agent_response_callback (Callable | None): A function that is called when a streaming response
                is produced by the agents.
        """
        self._manager = manager

        for member in members:
            if member.description is None:
                raise ValueError("All members must have a description.")

        super().__init__(
            members=members,
            name=name,
            description=description,
            input_transform=input_transform,
            output_transform=output_transform,
            agent_response_callback=agent_response_callback,
            streaming_agent_response_callback=streaming_agent_response_callback,
        )

    @override
    async def _start(
        self,
        task: DefaultTypeAlias,
        runtime: CoreRuntime,
        internal_topic_type: str,
        cancellation_token: CancellationToken,
    ) -> None:
        """Start the Magentic pattern."""
        if not isinstance(task, ChatMessageContent):
            # Magentic One only supports ChatMessageContent as input.
            raise ValueError("The task must be a ChatMessageContent object.")

        target_actor_id = await runtime.get(self._get_manager_actor_type(internal_topic_type))
        await runtime.send_message(
            MagenticStartMessage(body=task),
            target_actor_id,
            cancellation_token=cancellation_token,
        )

    @override
    async def _prepare(
        self,
        runtime: CoreRuntime,
        internal_topic_type: str,
        result_callback: Callable[[DefaultTypeAlias], Awaitable[None]],
    ) -> None:
        """Register the actors and orchestrations with the runtime and add the required subscriptions."""
        await self._register_members(runtime, internal_topic_type)
        await self._register_manager(runtime, internal_topic_type, result_callback=result_callback)
        await self._add_subscriptions(runtime, internal_topic_type)

    async def _register_members(self, runtime: CoreRuntime, internal_topic_type: str) -> None:
        """Register the agents."""
        await asyncio.gather(*[
            MagenticAgentActor.register(
                runtime,
                self._get_agent_actor_type(agent, internal_topic_type),
                lambda agent=agent: MagenticAgentActor(  # type: ignore[misc]
                    agent,
                    internal_topic_type,
                    self._agent_response_callback,
                    self._streaming_agent_response_callback,
                ),
            )
            for agent in self._members
        ])

    async def _register_manager(
        self,
        runtime: CoreRuntime,
        internal_topic_type: str,
        result_callback: Callable[[DefaultTypeAlias], Awaitable[None]] | None = None,
    ) -> None:
        """Register the group chat manager."""
        await MagenticManagerActor.register(
            runtime,
            self._get_manager_actor_type(internal_topic_type),
            lambda: MagenticManagerActor(
                self._manager,
                internal_topic_type=internal_topic_type,
                participant_descriptions={agent.name: agent.description for agent in self._members},  # type: ignore[misc]
                result_callback=result_callback,
            ),
        )

    async def _add_subscriptions(self, runtime: CoreRuntime, internal_topic_type: str) -> None:
        subscriptions: list[TypeSubscription] = []
        for agent in self._members:
            subscriptions.append(
                TypeSubscription(internal_topic_type, self._get_agent_actor_type(agent, internal_topic_type))
            )
        subscriptions.append(TypeSubscription(internal_topic_type, self._get_manager_actor_type(internal_topic_type)))

        await asyncio.gather(*[runtime.add_subscription(sub) for sub in subscriptions])

    def _get_agent_actor_type(self, agent: Agent, internal_topic_type: str) -> str:
        """Get the actor type for an agent.

        The type is appended with the internal topic type to ensure uniqueness in the runtime
        that may be shared by multiple orchestrations.
        """
        return f"{agent.name}_{internal_topic_type}"

    def _get_manager_actor_type(self, internal_topic_type: str) -> str:
        """Get the actor type for the group chat manager.

        The type is appended with the internal topic type to ensure uniqueness in the runtime
        that may be shared by multiple orchestrations.
        """
        return f"{MagenticManagerActor.__name__}_{internal_topic_type}"


# endregion MagenticOrchestration
