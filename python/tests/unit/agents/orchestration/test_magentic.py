# Copyright (c) Microsoft. All rights reserved.

import sys
from typing import Any, Literal
from unittest.mock import AsyncMock, patch

import pytest
from pydantic import BaseModel

from semantic_kernel.agents.orchestration.magentic import (
    MagenticContext,
    MagenticOrchestration,
    ProgressLedger,
    ProgressLedgerItem,
    StandardMagenticManager,
)
from semantic_kernel.agents.orchestration.orchestration_base import DefaultTypeAlias, OrchestrationResult
from semantic_kernel.agents.orchestration.prompts._magentic_prompts import (
    ORCHESTRATOR_FINAL_ANSWER_PROMPT,
    ORCHESTRATOR_PROGRESS_LEDGER_PROMPT,
    ORCHESTRATOR_TASK_LEDGER_FACTS_PROMPT,
    ORCHESTRATOR_TASK_LEDGER_FACTS_UPDATE_PROMPT,
    ORCHESTRATOR_TASK_LEDGER_FULL_PROMPT,
    ORCHESTRATOR_TASK_LEDGER_PLAN_PROMPT,
    ORCHESTRATOR_TASK_LEDGER_PLAN_UPDATE_PROMPT,
)
from semantic_kernel.agents.runtime.in_process.in_process_runtime import InProcessRuntime
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from tests.unit.agents.orchestration.conftest import MockAgent, MockRuntime


class MockChatCompletionService(ChatCompletionClientBase):
    """A mock chat completion service for testing purposes."""

    pass


class MockPromptExecutionSettings(PromptExecutionSettings):
    """A mock prompt execution settings class for testing purposes."""

    response_format: (
        dict[Literal["type"], Literal["text", "json_object"]] | dict[str, Any] | type[BaseModel] | type | None
    ) = None


# region MagenticOrchestration


async def test_init_member_without_description_throws():
    """Test the prepare method of the MagenticOrchestration with a member without description."""
    agent_a = MockAgent()
    agent_b = MockAgent()

    with pytest.raises(ValueError):
        MagenticOrchestration(
            members=[agent_a, agent_b],
            manager=StandardMagenticManager(
                chat_completion_service=MockChatCompletionService(ai_model_id="test"),
                prompt_execution_settings=MockPromptExecutionSettings(),
            ),
        )


async def test_prepare():
    """Test the prepare method of the MagenticOrchestration."""
    agent_a = MockAgent(description="test agent")
    agent_b = MockAgent(description="test agent")

    runtime = MockRuntime()

    package_path = "semantic_kernel.agents.orchestration.magentic"
    with (
        patch(f"{package_path}.MagenticOrchestration._start"),
        patch(f"{package_path}.MagenticAgentActor.register") as mock_agent_actor_register,
        patch(f"{package_path}.MagenticManagerActor.register") as mock_manager_actor_register,
        patch.object(runtime, "add_subscription") as mock_add_subscription,
    ):
        orchestration = MagenticOrchestration(
            members=[agent_a, agent_b],
            manager=StandardMagenticManager(
                chat_completion_service=MockChatCompletionService(ai_model_id="test"),
                prompt_execution_settings=MockPromptExecutionSettings(),
            ),
        )
        await orchestration.invoke(task="test_message", runtime=runtime)

        assert mock_agent_actor_register.call_count == 2
        assert mock_manager_actor_register.call_count == 1
        assert mock_add_subscription.call_count == 3


ManagerProgressList = [
    ProgressLedger(
        is_request_satisfied=ProgressLedgerItem(answer=False, reason="mock_reasoning"),
        is_in_loop=ProgressLedgerItem(answer=False, reason="mock_reasoning"),
        is_progress_being_made=ProgressLedgerItem(answer=True, reason="mock_reasoning"),
        next_speaker=ProgressLedgerItem(answer="agent_a", reason="mock_reasoning"),
        instruction_or_question=ProgressLedgerItem(answer="mock_instruction", reason="mock_reasoning"),
    ),
    ProgressLedger(
        is_request_satisfied=ProgressLedgerItem(answer=False, reason="mock_reasoning"),
        is_in_loop=ProgressLedgerItem(answer=False, reason="mock_reasoning"),
        is_progress_being_made=ProgressLedgerItem(answer=True, reason="mock_reasoning"),
        next_speaker=ProgressLedgerItem(answer="agent_b", reason="mock_reasoning"),
        instruction_or_question=ProgressLedgerItem(answer="mock_instruction", reason="mock_reasoning"),
    ),
    ProgressLedger(
        is_request_satisfied=ProgressLedgerItem(answer=True, reason="mock_reasoning"),
        is_in_loop=ProgressLedgerItem(answer=False, reason="mock_reasoning"),
        is_progress_being_made=ProgressLedgerItem(answer=True, reason="mock_reasoning"),
        next_speaker=ProgressLedgerItem(answer="N/A", reason="mock_reasoning"),
        instruction_or_question=ProgressLedgerItem(answer="mock_instruction", reason="mock_reasoning"),
    ),
]

ManagerProgressListStalling = [
    ProgressLedger(
        is_request_satisfied=ProgressLedgerItem(answer=False, reason="mock_reasoning"),
        is_in_loop=ProgressLedgerItem(answer=False, reason="mock_reasoning"),
        is_progress_being_made=ProgressLedgerItem(answer=True, reason="mock_reasoning"),
        next_speaker=ProgressLedgerItem(answer="agent_a", reason="mock_reasoning"),
        instruction_or_question=ProgressLedgerItem(answer="mock_instruction", reason="mock_reasoning"),
    ),
    ProgressLedger(
        is_request_satisfied=ProgressLedgerItem(answer=False, reason="mock_reasoning"),
        is_in_loop=ProgressLedgerItem(answer=True, reason="mock_reasoning"),  # is_in_loop=True
        is_progress_being_made=ProgressLedgerItem(answer=True, reason="mock_reasoning"),
        next_speaker=ProgressLedgerItem(answer="agent_a", reason="mock_reasoning"),
        instruction_or_question=ProgressLedgerItem(answer="mock_instruction", reason="mock_reasoning"),
    ),
    ProgressLedger(
        is_request_satisfied=ProgressLedgerItem(answer=False, reason="mock_reasoning"),
        is_in_loop=ProgressLedgerItem(answer=True, reason="mock_reasoning"),  # is_in_loop=True
        is_progress_being_made=ProgressLedgerItem(answer=True, reason="mock_reasoning"),
        next_speaker=ProgressLedgerItem(answer="N/A", reason="mock_reasoning"),
        instruction_or_question=ProgressLedgerItem(answer="mock_instruction", reason="mock_reasoning"),
    ),
    ProgressLedger(
        is_request_satisfied=ProgressLedgerItem(answer=False, reason="mock_reasoning"),
        is_in_loop=ProgressLedgerItem(answer=False, reason="mock_reasoning"),
        is_progress_being_made=ProgressLedgerItem(answer=True, reason="mock_reasoning"),
        next_speaker=ProgressLedgerItem(answer="agent_b", reason="mock_reasoning"),
        instruction_or_question=ProgressLedgerItem(answer="mock_instruction", reason="mock_reasoning"),
    ),
    ProgressLedger(
        is_request_satisfied=ProgressLedgerItem(answer=True, reason="mock_reasoning"),
        is_in_loop=ProgressLedgerItem(answer=False, reason="mock_reasoning"),
        is_progress_being_made=ProgressLedgerItem(answer=True, reason="mock_reasoning"),
        next_speaker=ProgressLedgerItem(answer="N/A", reason="mock_reasoning"),
        instruction_or_question=ProgressLedgerItem(answer="mock_instruction", reason="mock_reasoning"),
    ),
]

ManagerProgressListUnknownSpeaker = [
    ProgressLedger(
        is_request_satisfied=ProgressLedgerItem(answer=False, reason="mock_reasoning"),
        is_in_loop=ProgressLedgerItem(answer=False, reason="mock_reasoning"),
        is_progress_being_made=ProgressLedgerItem(answer=True, reason="mock_reasoning"),
        next_speaker=ProgressLedgerItem(answer="unknown", reason="mock_reasoning"),
        instruction_or_question=ProgressLedgerItem(answer="mock_instruction", reason="mock_reasoning"),
    ),
]


@pytest.mark.skipif(
    sys.version_info < (3, 11),
    reason="Python 3.10 doesn't bound the original function provided to the wraps argument of the patch object.",
)
async def test_invoke():
    """Test the invoke method of the MagenticOrchestration."""
    with (
        patch.object(MockAgent, "invoke_stream", wraps=MockAgent.invoke_stream, autospec=True) as mock_invoke_stream,
        patch.object(
            MockChatCompletionService, "get_chat_message_content", new_callable=AsyncMock
        ) as mock_get_chat_message_content,
        patch.object(
            StandardMagenticManager, "create_progress_ledger", new_callable=AsyncMock, side_effect=ManagerProgressList
        ),
    ):
        mock_get_chat_message_content.return_value = ChatMessageContent(role="assistant", content="mock_response")
        chat_completion_service = MockChatCompletionService(ai_model_id="test")
        prompt_execution_settings = MockPromptExecutionSettings()

        manager = StandardMagenticManager(
            chat_completion_service=chat_completion_service,
            prompt_execution_settings=prompt_execution_settings,
        )

        agent_a = MockAgent(name="agent_a", description="test agent")
        agent_b = MockAgent(name="agent_b", description="test agent")

        runtime = InProcessRuntime()
        runtime.start()

        try:
            orchestration = MagenticOrchestration(members=[agent_a, agent_b], manager=manager)
            orchestration_result = await orchestration.invoke(task="test_message", runtime=runtime)
            result = await orchestration_result.get()
        finally:
            await runtime.stop_when_idle()

        assert isinstance(orchestration_result, OrchestrationResult)
        assert isinstance(result, ChatMessageContent)
        assert result.role == AuthorRole.ASSISTANT
        assert result.content == "mock_response"

        assert mock_invoke_stream.call_count == 2
        assert mock_get_chat_message_content.call_count == 3


async def test_invoke_with_list_error():
    """Test the invoke method of the MagenticOrchestration with a list of messages which raises an error."""
    chat_completion_service = MockChatCompletionService(ai_model_id="test")
    prompt_execution_settings = MockPromptExecutionSettings()

    manager = StandardMagenticManager(
        chat_completion_service=chat_completion_service,
        prompt_execution_settings=prompt_execution_settings,
    )

    agent_a = MockAgent(name="agent_a", description="test agent")
    agent_b = MockAgent(name="agent_b", description="test agent")

    messages = [
        ChatMessageContent(role=AuthorRole.USER, content="test_message_1"),
        ChatMessageContent(role=AuthorRole.USER, content="test_message_2"),
    ]

    runtime = MockRuntime()

    package_path = "semantic_kernel.agents.orchestration.magentic"
    with (
        patch(f"{package_path}.MagenticAgentActor.register"),
        patch(f"{package_path}.MagenticManagerActor.register"),
        patch.object(runtime, "add_subscription"),
        pytest.raises(ValueError),
    ):
        orchestration = MagenticOrchestration(members=[agent_a, agent_b], manager=manager)
        orchestration_result = await orchestration.invoke(task=messages, runtime=runtime)
        await orchestration_result.get()


@pytest.mark.skipif(
    sys.version_info < (3, 11),
    reason="Python 3.10 doesn't bound the original function provided to the wraps argument of the patch object.",
)
async def test_invoke_with_response_callback():
    """Test the invoke method of the MagenticOrchestration with a response callback."""

    runtime = InProcessRuntime()
    runtime.start()

    responses: list[DefaultTypeAlias] = []
    with (
        patch.object(
            MockChatCompletionService, "get_chat_message_content", new_callable=AsyncMock
        ) as mock_get_chat_message_content,
        patch.object(
            StandardMagenticManager, "create_progress_ledger", new_callable=AsyncMock, side_effect=ManagerProgressList
        ),
    ):
        mock_get_chat_message_content.return_value = ChatMessageContent(role="assistant", content="mock_response")

        agent_a = MockAgent(name="agent_a", description="test agent")
        agent_b = MockAgent(name="agent_b", description="test agent")

        try:
            orchestration = MagenticOrchestration(
                members=[agent_a, agent_b],
                manager=StandardMagenticManager(
                    chat_completion_service=MockChatCompletionService(ai_model_id="test"),
                    prompt_execution_settings=MockPromptExecutionSettings(),
                ),
                agent_response_callback=lambda x: responses.append(x),
            )
            orchestration_result = await orchestration.invoke(task="test_message", runtime=runtime)
            await orchestration_result.get(1.0)
        finally:
            await runtime.stop_when_idle()

        assert len(responses) == 2
        assert all(isinstance(item, ChatMessageContent) for item in responses)
        assert all(item.content == "mock_response" for item in responses)


@pytest.mark.skipif(
    sys.version_info < (3, 11),
    reason="Python 3.10 doesn't bound the original function provided to the wraps argument of the patch object.",
)
async def test_invoke_with_streaming_response_callback():
    """Test the invoke method of the MagenticOrchestration with a streaming response callback."""

    runtime = InProcessRuntime()
    runtime.start()

    responses: dict[str, list[StreamingChatMessageContent]] = {}

    with (
        patch.object(
            MockChatCompletionService, "get_chat_message_content", new_callable=AsyncMock
        ) as mock_get_chat_message_content,
        patch.object(
            StandardMagenticManager, "create_progress_ledger", new_callable=AsyncMock, side_effect=ManagerProgressList
        ),
    ):
        mock_get_chat_message_content.return_value = ChatMessageContent(role="assistant", content="mock_response")

        agent_a = MockAgent(name="agent_a", description="test agent")
        agent_b = MockAgent(name="agent_b", description="test agent")

        try:
            orchestration = MagenticOrchestration(
                members=[agent_a, agent_b],
                manager=StandardMagenticManager(
                    chat_completion_service=MockChatCompletionService(ai_model_id="test"),
                    prompt_execution_settings=MockPromptExecutionSettings(),
                ),
                streaming_agent_response_callback=lambda x, _: responses.setdefault(x.name, []).append(x),
            )
            orchestration_result = await orchestration.invoke(task="test_message", runtime=runtime)
            await orchestration_result.get(1.0)
        finally:
            await runtime.stop_when_idle()

        assert len(responses[agent_a.name]) == 2
        assert len(responses[agent_b.name]) == 2

        assert all(isinstance(item, StreamingChatMessageContent) for item in responses[agent_a.name])
        assert all(isinstance(item, StreamingChatMessageContent) for item in responses[agent_b.name])

        agent_a_response = sum(responses[agent_a.name][1:], responses[agent_a.name][0])
        assert agent_a_response.content == "mock_response"
        agent_b_response = sum(responses[agent_b.name][1:], responses[agent_b.name][0])
        assert agent_b_response.content == "mock_response"


@pytest.mark.skipif(
    sys.version_info < (3, 11),
    reason="Python 3.10 doesn't bound the original function provided to the wraps argument of the patch object.",
)
async def test_invoke_with_max_stall_count_exceeded():
    """ "Test the invoke method of the MagenticOrchestration with max stall count exceeded."""
    runtime = InProcessRuntime()
    runtime.start()

    with (
        patch.object(MockAgent, "invoke_stream", wraps=MockAgent.invoke_stream, autospec=True) as mock_invoke_stream,
        patch.object(
            MockChatCompletionService, "get_chat_message_content", new_callable=AsyncMock
        ) as mock_get_chat_message_content,
        patch.object(
            StandardMagenticManager,
            "create_progress_ledger",
            new_callable=AsyncMock,
            side_effect=ManagerProgressListStalling,
        ),
    ):
        mock_get_chat_message_content.return_value = ChatMessageContent(role="assistant", content="mock_response")

        agent_a = MockAgent(name="agent_a", description="test agent")
        agent_b = MockAgent(name="agent_b", description="test agent")

        try:
            orchestration = MagenticOrchestration(
                members=[agent_a, agent_b],
                manager=StandardMagenticManager(
                    chat_completion_service=MockChatCompletionService(ai_model_id="test"),
                    prompt_execution_settings=MockPromptExecutionSettings(),
                    max_stall_count=1,
                ),
            )
            orchestration_result = await orchestration.invoke(task="test_message", runtime=runtime)
            await orchestration_result.get(1.0)
        finally:
            await runtime.stop_when_idle()

        assert mock_invoke_stream.call_count == 3
        # Exceeding max stall count will trigger replanning, which will recreate the facts and plan,
        # resulting in two additional calls to get_chat_message_content compared to the `test_invoke` test.
        assert mock_get_chat_message_content.call_count == 5


@pytest.mark.skipif(
    sys.version_info < (3, 11),
    reason="Python 3.10 doesn't bound the original function provided to the wraps argument of the patch object.",
)
async def test_invoke_with_max_round_count_exceeded():
    """ "Test the invoke method of the MagenticOrchestration with max round count exceeded."""
    runtime = InProcessRuntime()
    runtime.start()

    with (
        patch.object(MockAgent, "invoke_stream", wraps=MockAgent.invoke_stream, autospec=True) as mock_invoke_stream,
        patch.object(
            MockChatCompletionService, "get_chat_message_content", new_callable=AsyncMock
        ) as mock_get_chat_message_content,
        patch.object(
            StandardMagenticManager,
            "create_progress_ledger",
            new_callable=AsyncMock,
            side_effect=ManagerProgressListStalling,
        ),
    ):
        mock_get_chat_message_content.return_value = ChatMessageContent(role="assistant", content="mock_response")

        agent_a = MockAgent(name="agent_a", description="test agent")
        agent_b = MockAgent(name="agent_b", description="test agent")

        try:
            orchestration = MagenticOrchestration(
                members=[agent_a, agent_b],
                manager=StandardMagenticManager(
                    chat_completion_service=MockChatCompletionService(ai_model_id="test"),
                    prompt_execution_settings=MockPromptExecutionSettings(),
                    max_round_count=1,
                ),
            )
            orchestration_result = await orchestration.invoke(task="test_message", runtime=runtime)
            result = await orchestration_result.get(1.0)
        finally:
            await runtime.stop_when_idle()

        assert result.content == "Max round count reached."
        assert mock_invoke_stream.call_count == 1
        # Planning will be called once, so the facts and plan will be created once.
        assert mock_get_chat_message_content.call_count == 2


@pytest.mark.skipif(
    sys.version_info < (3, 11),
    reason="Python 3.10 doesn't bound the original function provided to the wraps argument of the patch object.",
)
async def test_invoke_with_max_reset_count_exceeded():
    """ "Test the invoke method of the MagenticOrchestration with max reset count exceeded."""
    runtime = InProcessRuntime()
    runtime.start()

    with (
        patch.object(MockAgent, "invoke_stream", wraps=MockAgent.invoke_stream, autospec=True) as mock_invoke_stream,
        patch.object(
            MockChatCompletionService, "get_chat_message_content", new_callable=AsyncMock
        ) as mock_get_chat_message_content,
        patch.object(
            StandardMagenticManager,
            "create_progress_ledger",
            new_callable=AsyncMock,
            side_effect=ManagerProgressListStalling,
        ),
    ):
        mock_get_chat_message_content.return_value = ChatMessageContent(role="assistant", content="mock_response")

        agent_a = MockAgent(name="agent_a", description="test agent")
        agent_b = MockAgent(name="agent_b", description="test agent")

        try:
            orchestration = MagenticOrchestration(
                members=[agent_a, agent_b],
                manager=StandardMagenticManager(
                    chat_completion_service=MockChatCompletionService(ai_model_id="test"),
                    prompt_execution_settings=MockPromptExecutionSettings(),
                    max_stall_count=0,  # No stall allowed
                    max_reset_count=0,  # No reset allowed
                ),
            )
            orchestration_result = await orchestration.invoke(task="test_message", runtime=runtime)
            result = await orchestration_result.get(1.0)
        finally:
            await runtime.stop_when_idle()

        assert result.content == "Max reset count reached."
        assert mock_invoke_stream.call_count == 1
        # Planning and replanning will be each called once, so the facts and plan will be created twice.
        assert mock_get_chat_message_content.call_count == 4


@pytest.mark.skipif(
    sys.version_info < (3, 11),
    reason="Python 3.10 doesn't bound the original function provided to the wraps argument of the patch object.",
)
async def test_invoke_with_unknown_speaker():
    """Test the invoke method of the MagenticOrchestration with an unknown speaker."""
    runtime = InProcessRuntime()
    runtime.start()

    with (
        patch.object(
            MockChatCompletionService, "get_chat_message_content", new_callable=AsyncMock
        ) as mock_get_chat_message_content,
        patch.object(
            StandardMagenticManager,
            "create_progress_ledger",
            new_callable=AsyncMock,
            side_effect=ManagerProgressListUnknownSpeaker,
        ),
        pytest.raises(ValueError),
    ):
        mock_get_chat_message_content.return_value = ChatMessageContent(role="assistant", content="mock_response")

        agent_a = MockAgent(name="agent_a", description="test agent")
        agent_b = MockAgent(name="agent_b", description="test agent")

        try:
            orchestration = MagenticOrchestration(
                members=[agent_a, agent_b],
                manager=StandardMagenticManager(
                    chat_completion_service=MockChatCompletionService(ai_model_id="test"),
                    prompt_execution_settings=MockPromptExecutionSettings(),
                ),
            )
            orchestration_result = await orchestration.invoke(task="test_message", runtime=runtime)
            await orchestration_result.get()
        finally:
            await runtime.stop_when_idle()


# endregion MagenticOrchestration

# region StandardMagenticManager


def test_standard_magentic_manager_init():
    """Test the initialization of the StandardMagenticManager."""
    chat_completion_service = MockChatCompletionService(ai_model_id="test")
    prompt_execution_settings = MockPromptExecutionSettings()

    manager = StandardMagenticManager(
        chat_completion_service=chat_completion_service,
        prompt_execution_settings=prompt_execution_settings,
    )

    assert manager.max_stall_count > 0
    assert manager.max_reset_count is None
    assert manager.max_round_count is None
    assert (
        manager.task_ledger_facts_prompt is not None
        and manager.task_ledger_facts_prompt == ORCHESTRATOR_TASK_LEDGER_FACTS_PROMPT
    )
    assert (
        manager.task_ledger_plan_prompt is not None
        and manager.task_ledger_plan_prompt == ORCHESTRATOR_TASK_LEDGER_PLAN_PROMPT
    )
    assert (
        manager.task_ledger_full_prompt is not None
        and manager.task_ledger_full_prompt == ORCHESTRATOR_TASK_LEDGER_FULL_PROMPT
    )
    assert (
        manager.task_ledger_facts_update_prompt is not None
        and manager.task_ledger_facts_update_prompt == ORCHESTRATOR_TASK_LEDGER_FACTS_UPDATE_PROMPT
    )
    assert (
        manager.task_ledger_plan_update_prompt is not None
        and manager.task_ledger_plan_update_prompt == ORCHESTRATOR_TASK_LEDGER_PLAN_UPDATE_PROMPT
    )
    assert (
        manager.progress_ledger_prompt is not None
        and manager.progress_ledger_prompt == ORCHESTRATOR_PROGRESS_LEDGER_PROMPT
    )
    assert manager.final_answer_prompt is not None and manager.final_answer_prompt == ORCHESTRATOR_FINAL_ANSWER_PROMPT


def test_standard_magentic_manager_init_with_custom_prompts():
    """Test the initialization of the StandardMagenticManager with custom prompts."""
    chat_completion_service = MockChatCompletionService(ai_model_id="test")
    prompt_execution_settings = MockPromptExecutionSettings()

    manager = StandardMagenticManager(
        chat_completion_service=chat_completion_service,
        prompt_execution_settings=prompt_execution_settings,
        task_ledger_facts_prompt="custom_task_ledger_facts_prompt",
        task_ledger_plan_prompt="custom_task_ledger_plan_prompt",
        task_ledger_full_prompt="custom_task_ledger_full_prompt",
        task_ledger_facts_update_prompt="custom_task_ledger_facts_update_prompt",
        task_ledger_plan_update_prompt="custom_task_ledger_plan_update_prompt",
        progress_ledger_prompt="custom_progress_ledger_prompt",
        final_answer_prompt="custom_final_answer_prompt",
    )

    assert manager.task_ledger_facts_prompt == "custom_task_ledger_facts_prompt"
    assert manager.task_ledger_plan_prompt == "custom_task_ledger_plan_prompt"
    assert manager.task_ledger_full_prompt == "custom_task_ledger_full_prompt"
    assert manager.task_ledger_facts_update_prompt == "custom_task_ledger_facts_update_prompt"
    assert manager.task_ledger_plan_update_prompt == "custom_task_ledger_plan_update_prompt"
    assert manager.progress_ledger_prompt == "custom_progress_ledger_prompt"
    assert manager.final_answer_prompt == "custom_final_answer_prompt"


def test_standard_magentic_manager_init_with_invalid_prompt_execution_settings():
    """Test the initialization of the StandardMagenticManager with invalid prompt execution settings."""
    chat_completion_service = MockChatCompletionService(ai_model_id="test")
    prompt_execution_settings = PromptExecutionSettings()

    with pytest.raises(ValueError):
        StandardMagenticManager(
            chat_completion_service=chat_completion_service,
            prompt_execution_settings=prompt_execution_settings,
        )


def test_standard_magentic_manager_init_without_prompt_execution_settings():
    """Test the initialization of the StandardMagenticManager without prompt execution settings."""
    # The default prompt execution settings of the mock chat completion service
    # does not support structured output.
    chat_completion_service = MockChatCompletionService(ai_model_id="test")

    with pytest.raises(ValueError):
        StandardMagenticManager(chat_completion_service=chat_completion_service)


async def test_standard_magentic_manager_plan():
    """Test the plan method of the StandardMagenticManager."""

    with patch.object(
        MockChatCompletionService, "get_chat_message_content", new_callable=AsyncMock
    ) as mock_get_chat_message_content:
        mock_get_chat_message_content.return_value = ChatMessageContent(role="assistant", content="mock_response")
        chat_completion_service = MockChatCompletionService(ai_model_id="test")
        prompt_execution_settings = MockPromptExecutionSettings()

        manager = StandardMagenticManager(
            chat_completion_service=chat_completion_service,
            prompt_execution_settings=prompt_execution_settings,
            task_ledger_facts_prompt="custom_task_ledger_facts_prompt",
            task_ledger_plan_prompt="custom_task_ledger_plan_prompt {{$team}}",
        )

        magentic_context = MagenticContext(
            chat_history=ChatHistory(),
            task=ChatMessageContent(role="user", content="test_message"),
            participant_descriptions={"agent_a": "test_agent_a", "agent_b": "test_agent_b"},
        )

        task_ledger = await manager.plan(magentic_context.model_copy(deep=True))

        assert isinstance(task_ledger, ChatMessageContent)
        assert task_ledger.content.count("mock_response") == 2
        assert "test_message" in task_ledger.content
        assert "{'agent_a': 'test_agent_a', 'agent_b': 'test_agent_b'}" in task_ledger.content

        assert mock_get_chat_message_content.call_count == 2
        assert (
            mock_get_chat_message_content.call_args_list[0][0][0].messages[0].content
            == "custom_task_ledger_facts_prompt"
        )
        assert (
            mock_get_chat_message_content.call_args_list[1][0][0].messages[2].content
            == "custom_task_ledger_plan_prompt {'agent_a': 'test_agent_a', 'agent_b': 'test_agent_b'}"
        )


async def test_standard_magentic_manager_replan():
    """Test the replan method of the StandardMagenticManager."""

    with patch.object(
        MockChatCompletionService, "get_chat_message_content", new_callable=AsyncMock
    ) as mock_get_chat_message_content:
        mock_get_chat_message_content.return_value = ChatMessageContent(role="assistant", content="mock_response")

        chat_completion_service = MockChatCompletionService(ai_model_id="test")
        prompt_execution_settings = MockPromptExecutionSettings()

        manager = StandardMagenticManager(
            chat_completion_service=chat_completion_service,
            prompt_execution_settings=prompt_execution_settings,
            task_ledger_facts_update_prompt="custom_task_ledger_facts_prompt {{$old_facts}}",
            task_ledger_plan_update_prompt="custom_task_ledger_plan_prompt {{$team}}",
        )

        magentic_context = MagenticContext(
            chat_history=ChatHistory(),
            task=ChatMessageContent(role="user", content="test_message"),
            participant_descriptions={"agent_a": "test_agent_a", "agent_b": "test_agent_b"},
        )

        # Need to plan before replanning
        _ = await manager.plan(magentic_context.model_copy(deep=True))
        task_ledger = await manager.replan(magentic_context.model_copy(deep=True))

        assert isinstance(task_ledger, ChatMessageContent)
        assert task_ledger.content.count("mock_response") == 2
        assert "test_message" in task_ledger.content
        assert "{'agent_a': 'test_agent_a', 'agent_b': 'test_agent_b'}" in task_ledger.content

        assert mock_get_chat_message_content.call_count == 4
        assert (
            mock_get_chat_message_content.call_args_list[2][0][0].messages[0].content
            == "custom_task_ledger_facts_prompt mock_response"
        )
        assert (
            mock_get_chat_message_content.call_args_list[3][0][0].messages[2].content
            == "custom_task_ledger_plan_prompt {'agent_a': 'test_agent_a', 'agent_b': 'test_agent_b'}"
        )


async def test_standard_magentic_manager_replan_without_plan():
    """Test the replan method of the StandardMagenticManager."""

    chat_completion_service = MockChatCompletionService(ai_model_id="test")
    prompt_execution_settings = MockPromptExecutionSettings()

    manager = StandardMagenticManager(
        chat_completion_service=chat_completion_service,
        prompt_execution_settings=prompt_execution_settings,
    )

    magentic_context = MagenticContext(
        chat_history=ChatHistory(),
        task=ChatMessageContent(role="user", content="test_message"),
        participant_descriptions={"agent_a": "test_agent_a", "agent_b": "test_agent_b"},
    )

    with pytest.raises(RuntimeError):
        _ = await manager.replan(magentic_context.model_copy(deep=True))


async def test_standard_magentic_manager_create_progress_ledger():
    """Test the create_progress_ledger method of the StandardMagenticManager."""

    mock_progress_ledger = ProgressLedger(
        is_request_satisfied=ProgressLedgerItem(answer=False, reason="mock_reasoning"),
        is_in_loop=ProgressLedgerItem(answer=False, reason="mock_reasoning"),
        is_progress_being_made=ProgressLedgerItem(answer=False, reason="mock_reasoning"),
        next_speaker=ProgressLedgerItem(answer="agent_a", reason="mock_reasoning"),
        instruction_or_question=ProgressLedgerItem(answer="mock_instruction", reason="mock_reasoning"),
    )

    with patch.object(
        MockChatCompletionService, "get_chat_message_content", new_callable=AsyncMock
    ) as mock_get_chat_message_content:
        mock_get_chat_message_content.return_value = ChatMessageContent(
            role="assistant", content=mock_progress_ledger.model_dump_json()
        )

        chat_completion_service = MockChatCompletionService(ai_model_id="test")
        prompt_execution_settings = MockPromptExecutionSettings()

        manager = StandardMagenticManager(
            chat_completion_service=chat_completion_service,
            prompt_execution_settings=prompt_execution_settings,
        )

        magentic_context = MagenticContext(
            chat_history=ChatHistory(),
            task=ChatMessageContent(role="user", content="test_message"),
            participant_descriptions={"agent_a": "test_agent_a", "agent_b": "test_agent_b"},
        )

        progress_ledger = await manager.create_progress_ledger(magentic_context.model_copy(deep=True))

        assert isinstance(progress_ledger, ProgressLedger)
        assert progress_ledger == mock_progress_ledger

        assert (
            "{'agent_a': 'test_agent_a', 'agent_b': 'test_agent_b'}"
            in mock_get_chat_message_content.call_args_list[0][0][0].messages[0].content
        )
        assert "agent_a, agent_b" in mock_get_chat_message_content.call_args_list[0][0][0].messages[0].content
        assert (
            magentic_context.task.content in mock_get_chat_message_content.call_args_list[0][0][0].messages[0].content
        )
        assert mock_get_chat_message_content.call_args_list[0][0][1].extension_data["response_format"] == ProgressLedger


# endregion MagenticManager
