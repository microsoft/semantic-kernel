# Copyright (c) Microsoft. All rights reserved.

import asyncio
import logging
import sys
from abc import ABC, abstractmethod
from collections.abc import Awaitable, Callable

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
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel import Kernel
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.prompt_template.kernel_prompt_template import KernelPromptTemplate
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig

if sys.version_info >= (3, 12):
    from typing import override  # pragma: no cover
else:
    from typing_extensions import override  # pragma: no cover

logger: logging.Logger = logging.getLogger(__name__)


# region Messages and Types


class MagenticStartMessage(KernelBaseModel):
    """A message to start a magentic group chat."""

    body: ChatMessageContent


class MagenticRequestMessage(KernelBaseModel):
    """A request message type for agents in a magentic group chat."""

    agent_name: str


class MagenticResponseMessage(KernelBaseModel):
    """A response message type from agents in a magentic group chat."""

    body: ChatMessageContent


class MagenticResetMessage(KernelBaseModel):
    """A message to reset a participant's chat history in a magentic group chat."""

    pass


class ProgressLedgerItem(KernelBaseModel):
    """A progress ledger item."""

    reason: str
    answer: str | bool


class ProgressLedger(KernelBaseModel):
    """A progress ledger."""

    is_request_satisfied: ProgressLedgerItem
    is_in_loop: ProgressLedgerItem
    is_progress_being_made: ProgressLedgerItem
    next_speaker: ProgressLedgerItem
    instruction_or_question: ProgressLedgerItem


# endregion Messages and Types

# region MagenticManager


class MagenticManager(KernelBaseModel, ABC):
    """Base class for the Magentic One manager."""

    @abstractmethod
    async def create_facts_and_plan(
        self,
        chat_history: ChatHistory,
        task: ChatMessageContent,
        participant_descriptions: dict[str, str],
        old_facts: ChatMessageContent | None = None,
    ) -> tuple[ChatMessageContent, ChatMessageContent]:
        """Create facts and plan for the task.

        Args:
            chat_history (ChatHistory): The chat history. This chat history will be modified by the function.
            task (ChatMessageContent): The task.
            participant_descriptions (dict[str, str]): The participant descriptions.
            old_facts (ChatMessageContent | None): The old facts. If provided, the facts and plan update
                prompts will be used.

        Returns:
            tuple[ChatMessageContent, ChatMessageContent]: The facts and plan.
        """
        ...

    @abstractmethod
    async def create_task_ledger(
        self,
        task: ChatMessageContent,
        facts: ChatMessageContent,
        plan: ChatMessageContent,
        participant_descriptions: dict[str, str],
    ) -> str:
        """Create a task ledger.

        Args:
            task (ChatMessageContent): The task.
            facts (ChatMessageContent): The facts.
            plan (ChatMessageContent): The plan.
            participant_descriptions (dict[str, str]): The participant descriptions.

        Returns:
            str: The task ledger.
        """
        ...

    @abstractmethod
    async def create_progress_ledger(
        self,
        chat_history: ChatHistory,
        task: ChatMessageContent,
        participant_descriptions: dict[str, str],
    ) -> ProgressLedger:
        """Create a progress ledger.

        Args:
            chat_history (ChatHistory): The chat history. This chat history will be modified by the function.
            task (ChatMessageContent): The task.
            participant_descriptions (dict[str, str]): The participant descriptions.

        Returns:
            ProgressLedger: The progress ledger.
        """
        ...

    @abstractmethod
    async def prepare_final_answer(self, chat_history: ChatHistory, task: ChatMessageContent) -> ChatMessageContent:
        """Prepare the final answer.

        Args:
            chat_history (ChatHistory): The chat history. This chat history will be modified by the function.
            task (ChatMessageContent): The task.

        Returns:
            ChatMessageContent: The final answer.
        """
        ...


class StandardMagenticManager(MagenticManager):
    """Container for the Magentic pattern."""

    chat_completion_service: ChatCompletionClientBase
    prompt_execution_settings: PromptExecutionSettings

    max_stall_count: int = 3

    task_ledger_facts_prompt: str = ORCHESTRATOR_TASK_LEDGER_FACTS_PROMPT
    task_ledger_plan_prompt: str = ORCHESTRATOR_TASK_LEDGER_PLAN_PROMPT
    task_ledger_full_prompt: str = ORCHESTRATOR_TASK_LEDGER_FULL_PROMPT
    task_ledger_facts_update_prompt: str = ORCHESTRATOR_TASK_LEDGER_FACTS_UPDATE_PROMPT
    task_ledger_plan_update_prompt: str = ORCHESTRATOR_TASK_LEDGER_PLAN_UPDATE_PROMPT
    progress_ledger_prompt: str = ORCHESTRATOR_PROGRESS_LEDGER_PROMPT
    final_answer_prompt: str = ORCHESTRATOR_FINAL_ANSWER_PROMPT

    @override
    async def create_facts_and_plan(
        self,
        chat_history: ChatHistory,
        task: ChatMessageContent,
        participant_descriptions: dict[str, str],
        old_facts: ChatMessageContent | None = None,
    ) -> tuple[ChatMessageContent, ChatMessageContent]:
        """Create facts and plan for the task.

        Args:
            chat_history (ChatHistory): The chat history. This chat history will be modified by the function.
            task (ChatMessageContent): The task.
            participant_descriptions (dict[str, str]): The participant descriptions.
            old_facts (ChatMessageContent | None): The old facts. If provided, the facts and plan update
                prompts will be used.

        Returns:
            tuple[ChatMessageContent, ChatMessageContent]: The facts and plan.
        """
        # 1. Update the facts
        prompt_template = KernelPromptTemplate(
            prompt_template_config=PromptTemplateConfig(
                template=self.task_ledger_facts_update_prompt if old_facts else self.task_ledger_facts_prompt
            )
        )
        chat_history.add_message(
            ChatMessageContent(
                role=AuthorRole.USER,
                content=await prompt_template.render(
                    Kernel(),
                    KernelArguments(task=task.content, old_facts=old_facts.content)
                    if old_facts
                    else KernelArguments(task=task.content),
                ),
            )
        )
        facts = await self.chat_completion_service.get_chat_message_content(
            chat_history,
            self.prompt_execution_settings,
        )
        assert facts is not None  # nosec B101
        chat_history.add_message(facts)

        # 2. Update the plan
        prompt_template = KernelPromptTemplate(
            prompt_template_config=PromptTemplateConfig(
                template=self.task_ledger_plan_update_prompt if old_facts else self.task_ledger_plan_prompt
            )
        )
        chat_history.add_message(
            ChatMessageContent(
                role=AuthorRole.USER,
                content=await prompt_template.render(
                    Kernel(),
                    KernelArguments(team=participant_descriptions),
                ),
            )
        )
        plan = await self.chat_completion_service.get_chat_message_content(
            chat_history,
            self.prompt_execution_settings,
        )
        assert plan is not None  # nosec B101

        return facts, plan

    @override
    async def create_task_ledger(
        self,
        task: ChatMessageContent,
        facts: ChatMessageContent,
        plan: ChatMessageContent,
        participant_descriptions: dict[str, str],
    ) -> str:
        """Create a task ledger.

        Args:
            task (ChatMessageContent): The task.
            facts (ChatMessageContent): The facts.
            plan (ChatMessageContent): The plan.
            participant_descriptions (dict[str, str]): The participant descriptions.

        Returns:
            str: The task ledger.
        """
        prompt_template = KernelPromptTemplate(
            prompt_template_config=PromptTemplateConfig(template=self.task_ledger_full_prompt)
        )

        return await prompt_template.render(
            Kernel(),
            KernelArguments(
                task=task.content,
                team=participant_descriptions,
                facts=facts.content,
                plan=plan.content,
            ),
        )

    @override
    async def create_progress_ledger(
        self,
        chat_history: ChatHistory,
        task: ChatMessageContent,
        participant_descriptions: dict[str, str],
    ) -> ProgressLedger:
        """Create a progress ledger.

        Args:
            chat_history (ChatHistory): The chat history. This chat history will be modified by the function.
            task (ChatMessageContent): The task.
            participant_descriptions (dict[str, str]): The participant descriptions.

        Returns:
            ProgressLedger: The progress ledger.
        """
        prompt_template = KernelPromptTemplate(
            prompt_template_config=PromptTemplateConfig(template=self.progress_ledger_prompt)
        )
        progress_ledger_prompt = await prompt_template.render(
            Kernel(),
            KernelArguments(
                task=task.content,
                team=participant_descriptions,
                names=", ".join(participant_descriptions.keys()),
            ),
        )
        chat_history.add_message(ChatMessageContent(role=AuthorRole.USER, content=progress_ledger_prompt))

        prompt_execution_settings_clone = PromptExecutionSettings.from_prompt_execution_settings(
            self.prompt_execution_settings
        )
        prompt_execution_settings_clone.update_from_prompt_execution_settings(
            # TODO(@taochen): Double check how to make sure the service support json output.
            PromptExecutionSettings(extension_data={"response_format": ProgressLedger})
        )

        response = await self.chat_completion_service.get_chat_message_content(
            chat_history,
            prompt_execution_settings_clone,
        )
        assert response is not None  # nosec B101

        return ProgressLedger.model_validate_json(response.content)

    @override
    async def prepare_final_answer(self, chat_history: ChatHistory, task: ChatMessageContent) -> ChatMessageContent:
        """Prepare the final answer.

        Args:
            chat_history (ChatHistory): The chat history. This chat history will be modified by the function.
            task (ChatMessageContent): The task.

        Returns:
            ChatMessageContent: The final answer.
        """
        prompt_template = KernelPromptTemplate(
            prompt_template_config=PromptTemplateConfig(template=self.final_answer_prompt)
        )
        chat_history.add_message(
            ChatMessageContent(
                role=AuthorRole.USER,
                content=await prompt_template.render(Kernel(), KernelArguments(task=task)),
            )
        )

        response = await self.chat_completion_service.get_chat_message_content(
            chat_history,
            self.prompt_execution_settings,
        )
        assert response is not None  # nosec B101

        return response


# endregion MagenticManager

# region MagenticManagerActor


class MagenticManagerActor(ActorBase):
    """Actor for the Magentic One manager."""

    def __init__(
        self,
        manager: MagenticManager,
        internal_topic_type: str,
        participant_descriptions: dict[str, str],
        result_callback: Callable[[DefaultTypeAlias], Awaitable[None]] | None = None,
    ) -> None:
        """Initialize the Magentic One manager actor.

        Args:
            manager (MagenticManager): The Magentic One manager.
            internal_topic_type (str): The internal topic type.
            participant_descriptions (dict[str, str]): The participant descriptions.
            result_callback (Callable | None): A callback function to handle the final answer.
        """
        self._manager = manager
        self._internal_topic_type = internal_topic_type
        self._chat_history = ChatHistory()
        self._participant_descriptions = participant_descriptions
        self._result_callback = result_callback
        self._round_count = 0
        self._stall_count = 0

        super().__init__(description="Magentic One Manager")

    @message_handler
    async def _handle_start_message(self, message: MagenticStartMessage, ctx: MessageContext) -> None:
        """Handle the start message for the Magentic One manager."""
        logger.debug(f"{self.id}: Received Magentic One start message.")
        self._task = message.body
        self._facts, self._plan = await self._manager.create_facts_and_plan(
            self._chat_history.model_copy(deep=True),
            self._task,
            self._participant_descriptions,
        )

        await self._run_outer_loop(ctx.cancellation_token)

    @message_handler
    async def _handle_response_message(self, message: MagenticResponseMessage, ctx: MessageContext) -> None:
        if message.body.role != AuthorRole.USER:
            self._chat_history.add_message(
                ChatMessageContent(
                    role=AuthorRole.USER,
                    content=f"Transferred to {message.body.name}",
                )
            )
        self._chat_history.add_message(message.body)

        logger.debug(f"{self.id}: Running inner loop.")
        await self._run_inner_loop(ctx.cancellation_token)

    async def _run_outer_loop(self, cancellation_token: CancellationToken) -> None:
        # 1. Create a task ledger.
        task_ledger = await self._manager.create_task_ledger(
            self._task,
            self._facts,
            self._plan,
            self._participant_descriptions,
        )

        # 2. Publish the task ledger to the group chat.
        # Need to add the task ledger to the orchestrator's chat history
        # since the publisher won't receive the message it sends even though
        # the publisher also subscribes to the topic.
        self._chat_history.add_message(
            ChatMessageContent(
                role=AuthorRole.ASSISTANT,
                content=task_ledger,
                name=self.__class__.__name__,
            )
        )

        logger.debug(f"Initial task ledger:\n{task_ledger}")
        await self.publish_message(
            MagenticResponseMessage(
                body=self._chat_history.messages[-1],
            ),
            TopicId(self._internal_topic_type, self.id.key),
            cancellation_token=cancellation_token,
        )

        # 3. Start the inner loop.
        await self._run_inner_loop(cancellation_token)

    async def _run_inner_loop(self, cancellation_token: CancellationToken) -> None:
        self._round_count += 1

        # 1. Create a progress ledger
        current_progress_ledger = await self._manager.create_progress_ledger(
            self._chat_history.model_copy(deep=True),
            self._task,
            self._participant_descriptions,
        )
        logger.debug(f"Current progress ledger:\n{current_progress_ledger.model_dump_json(indent=2)}")

        # 2. Process the progress ledger
        # 2.1 Check for task completion
        if current_progress_ledger.is_request_satisfied.answer:
            logger.debug("Task completed.")
            await self._prepare_final_answer()
            return
        # 2.2 Check for stalling or looping
        if not current_progress_ledger.is_progress_being_made.answer or current_progress_ledger.is_in_loop.answer:
            self._stall_count += 1
        else:
            self._stall_count = max(0, self._stall_count - 1)

        if self._stall_count > self._manager.max_stall_count:
            logger.debug("Stalling detected. Resetting the task.")
            self._facts, self._plan = await self._manager.create_facts_and_plan(
                self._chat_history.model_copy(deep=True),
                self._task,
                self._participant_descriptions,
                old_facts=self._facts,
            )
            await self._reset_for_outer_loop(cancellation_token)
            logger.debug("Restarting outer loop.")
            await self._run_outer_loop(cancellation_token)
            return

        # 2.3 Publish for next step
        next_step = current_progress_ledger.instruction_or_question.answer
        self._chat_history.add_message(
            ChatMessageContent(
                role=AuthorRole.ASSISTANT,
                content=next_step if isinstance(next_step, str) else str(next_step),
                name=self.__class__.__name__,
            )
        )
        await self.publish_message(
            MagenticResponseMessage(
                body=self._chat_history.messages[-1],
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
        await self.publish_message(
            MagenticResetMessage(),
            TopicId(self._internal_topic_type, self.id.key),
            cancellation_token=cancellation_token,
        )
        self._chat_history.clear()
        self._stall_count = 0

    async def _prepare_final_answer(self) -> None:
        final_answer = await self._manager.prepare_final_answer(
            self._chat_history.model_copy(deep=True),
            self._task,
        )

        if self._result_callback:
            await self._result_callback(final_answer)


# endregion MagenticManagerActor

# region MagenticAgentActor


class MagenticAgentActor(AgentActorBase):
    """An agent actor that process messages in a Magentic One group chat."""

    @message_handler
    async def _handle_response_message(self, message: MagenticResponseMessage, ctx: MessageContext) -> None:
        logger.debug(f"{self.id}: Received response message.")
        if self._agent_thread is not None:
            if message.body.role != AuthorRole.USER:
                await self._agent_thread.on_new_message(
                    ChatMessageContent(
                        role=AuthorRole.USER,
                        content=f"Transferred to {message.body.name}",
                    )
                )
            await self._agent_thread.on_new_message(message.body)
        else:
            if message.body.role != AuthorRole.USER:
                self._chat_history.add_message(
                    ChatMessageContent(
                        role=AuthorRole.USER,
                        content=f"Transferred to {message.body.name}",
                    )
                )
            self._chat_history.add_message(message.body)

    @message_handler
    async def _handle_request_message(self, message: MagenticRequestMessage, ctx: MessageContext) -> None:
        if message.agent_name != self._agent.name:
            return

        logger.debug(f"{self.id}: Received request message.")
        if self._agent_thread is None:
            # Add a user message to steer the agent to respond more closely to the instructions.
            self._chat_history.add_message(
                ChatMessageContent(
                    role=AuthorRole.USER,
                    content=f"Transferred to {self._agent.name}, adopt the persona immediately.",
                )
            )
            response_item = await self._agent.get_response(messages=self._chat_history.messages)  # type: ignore[arg-type]
            self._agent_thread = response_item.thread
        else:
            # Add a user message to steer the agent to respond more closely to the instructions.
            new_message = ChatMessageContent(
                role=AuthorRole.USER,
                content=f"Transferred to {self._agent.name}, adopt the persona immediately.",
            )
            response_item = await self._agent.get_response(messages=new_message, thread=self._agent_thread)

        logger.debug(f"{self.id} responded with {response_item.message.content}.")
        await self._call_agent_response_callback(response_item.message)

        await self.publish_message(
            MagenticResponseMessage(body=response_item.message),
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


class MagenticOrchestration(OrchestrationBase[TIn, TOut]):
    """The Magentic One pattern orchestration."""

    def __init__(
        self,
        members: list[Agent],
        manager: MagenticManager,
        name: str | None = None,
        description: str | None = None,
        input_transform: Callable[[TIn], Awaitable[DefaultTypeAlias] | DefaultTypeAlias] | None = None,
        output_transform: Callable[[DefaultTypeAlias], Awaitable[TOut] | TOut] | None = None,
        agent_response_callback: Callable[[DefaultTypeAlias], Awaitable[None] | None] | None = None,
    ) -> None:
        """Initialize the Magentic One orchestration.

        Args:
            members (list[Agent | OrchestrationBase]): A list of agents or orchestration bases.
            manager (MagenticManager): The manager for the Magentic One pattern.
            name (str | None): The name of the orchestration.
            description (str | None): The description of the orchestration.
            input_transform (Callable | None): A function that transforms the external input message.
            output_transform (Callable | None): A function that transforms the internal output message.
            agent_response_callback (Callable | None): A function that is called when a response is produced
                by the agents.
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
        )

    @override
    async def _start(
        self,
        task: DefaultTypeAlias,
        runtime: CoreRuntime,
        internal_topic_type: str,
        cancellation_token: CancellationToken,
    ) -> None:
        """Start the Magentic One pattern.

        This ensures that all initial messages are sent to the individual actors
        and processed before the group chat begins. It's important because if the
        manager actor processes its start message too quickly (or other actors are
        too slow), it might send a request to the next agent before the other actors
        have the necessary context.
        """
        if not isinstance(task, ChatMessageContent):
            # Magentic One only supports ChatMessageContent as input.
            raise ValueError("The task must be a ChatMessageContent object.")

        async def send_start_message(agent: Agent) -> None:
            target_actor_id = await runtime.get(self._get_agent_actor_type(agent, internal_topic_type))
            await runtime.send_message(
                MagenticStartMessage(body=task),
                target_actor_id,
                cancellation_token=cancellation_token,
            )

        await asyncio.gather(*[send_start_message(agent) for agent in self._members])

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
