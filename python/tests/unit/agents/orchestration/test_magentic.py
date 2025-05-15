# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, patch
from uuid import uuid4

import pytest

from semantic_kernel.agents.orchestration.magentic import (
    MagenticManager,
    MagenticOrchestration,
    ProgressLedger,
    ProgressLedgerItem,
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
from semantic_kernel.contents.utils.author_role import AuthorRole
from tests.unit.agents.orchestration.conftest import MockAgent, MockRuntime


class MockChatCompletionService(ChatCompletionClientBase):
    """A mock chat completion service for testing purposes."""

    pass


# region MagenticOrchestration


async def test_init_member_without_description_throws():
    """Test the prepare method of the MagenticOrchestration with a member without description."""
    agent_a = MockAgent()
    agent_b = MockAgent()

    with pytest.raises(ValueError):
        MagenticOrchestration(
            members=[agent_a, agent_b],
            manager=MagenticManager(
                chat_completion_service=MockChatCompletionService(ai_model_id="test"),
                prompt_execution_settings=PromptExecutionSettings(),
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
            manager=MagenticManager(
                chat_completion_service=MockChatCompletionService(ai_model_id="test"),
                prompt_execution_settings=PromptExecutionSettings(),
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


async def test_invoke():
    """Test the invoke method of the MagenticOrchestration."""
    with (
        patch.object(MockAgent, "get_response", wraps=MockAgent.get_response, autospec=True) as mock_get_response,
        patch.object(
            MockChatCompletionService, "get_chat_message_content", new_callable=AsyncMock
        ) as mock_get_chat_message_content,
        patch.object(
            MagenticManager, "create_progress_ledger", new_callable=AsyncMock, side_effect=ManagerProgressList
        ),
    ):
        mock_get_chat_message_content.return_value = ChatMessageContent(role="assistant", content="mock_response")
        chat_completion_service = MockChatCompletionService(ai_model_id="test")
        prompt_execution_settings = PromptExecutionSettings()

        manager = MagenticManager(
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

        assert mock_get_response.call_count == 2
        assert mock_get_chat_message_content.call_count == 3


async def test_invoke_with_list_error():
    """Test the invoke method of the MagenticOrchestration with a list of messages which raises an error."""
    chat_completion_service = MockChatCompletionService(ai_model_id="test")
    prompt_execution_settings = PromptExecutionSettings()

    manager = MagenticManager(
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


async def test_invoke_with_response_callback():
    """Test the invoke method of the MagenticOrchestration with a response callback."""

    runtime = InProcessRuntime()
    runtime.start()

    responses: list[DefaultTypeAlias] = []
    with (
        patch.object(MockAgent, "get_response", wraps=MockAgent.get_response, autospec=True),
        patch.object(
            MockChatCompletionService, "get_chat_message_content", new_callable=AsyncMock
        ) as mock_get_chat_message_content,
        patch.object(
            MagenticManager, "create_progress_ledger", new_callable=AsyncMock, side_effect=ManagerProgressList
        ),
    ):
        mock_get_chat_message_content.return_value = ChatMessageContent(role="assistant", content="mock_response")

        agent_a = MockAgent(name="agent_a", description="test agent")
        agent_b = MockAgent(name="agent_b", description="test agent")

        try:
            orchestration = MagenticOrchestration(
                members=[agent_a, agent_b],
                manager=MagenticManager(
                    chat_completion_service=MockChatCompletionService(ai_model_id="test"),
                    prompt_execution_settings=PromptExecutionSettings(),
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


async def test_invoke_with_max_stall_count_exceeded():
    """ "Test the invoke method of the MagenticOrchestration with max stall count exceeded."""
    runtime = InProcessRuntime()
    runtime.start()

    with (
        patch.object(MockAgent, "get_response", wraps=MockAgent.get_response, autospec=True) as mock_get_response,
        patch.object(
            MockChatCompletionService, "get_chat_message_content", new_callable=AsyncMock
        ) as mock_get_chat_message_content,
        patch.object(
            MagenticManager,
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
                manager=MagenticManager(
                    chat_completion_service=MockChatCompletionService(ai_model_id="test"),
                    prompt_execution_settings=PromptExecutionSettings(),
                    max_stall_count=1,
                ),
            )
            orchestration_result = await orchestration.invoke(task="test_message", runtime=runtime)
            await orchestration_result.get(1.0)
        finally:
            await runtime.stop_when_idle()

        assert mock_get_response.call_count == 3
        # Exceeding max stall count will trigger replanning, which will recreate the facts and plan,
        # resulting in two additional calls to get_chat_message_content compared to the `test_invoke` test.
        assert mock_get_chat_message_content.call_count == 5


async def test_invoke_with_unknown_speaker():
    """Test the invoke method of the MagenticOrchestration with an unknown speaker."""
    runtime = InProcessRuntime()
    runtime.start()

    with (
        patch.object(MockAgent, "get_response", wraps=MockAgent.get_response, autospec=True),
        patch.object(
            MockChatCompletionService, "get_chat_message_content", new_callable=AsyncMock
        ) as mock_get_chat_message_content,
        patch.object(
            MagenticManager,
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
                manager=MagenticManager(
                    chat_completion_service=MockChatCompletionService(ai_model_id="test"),
                    prompt_execution_settings=PromptExecutionSettings(),
                ),
            )
            orchestration_result = await orchestration.invoke(task="test_message", runtime=runtime)
            await orchestration_result.get()
        finally:
            await runtime.stop_when_idle()


# endregion MagenticOrchestration

# region MagenticManager


def test_magentic_manager_init():
    """Test the initialization of the MagenticManager."""
    chat_completion_service = MockChatCompletionService(ai_model_id="test")
    prompt_execution_settings = PromptExecutionSettings()

    manager = MagenticManager(
        chat_completion_service=chat_completion_service,
        prompt_execution_settings=prompt_execution_settings,
    )

    assert manager.max_stall_count > 0
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


def test_magentic_manager_init_with_custom_prompts():
    """Test the initialization of the MagenticManager with custom prompts."""
    chat_completion_service = MockChatCompletionService(ai_model_id="test")
    prompt_execution_settings = PromptExecutionSettings()

    manager = MagenticManager(
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


async def test_magentic_manager_create_facts_and_prompt():
    """Test the create_facts_and_prompt method of the MagenticManager."""

    with patch.object(
        MockChatCompletionService, "get_chat_message_content", new_callable=AsyncMock
    ) as mock_get_chat_message_content:
        mock_get_chat_message_content.return_value = ChatMessageContent(role="assistant", content="mock_response")
        chat_completion_service = MockChatCompletionService(ai_model_id="test")
        prompt_execution_settings = PromptExecutionSettings()

        manager = MagenticManager(
            chat_completion_service=chat_completion_service,
            prompt_execution_settings=prompt_execution_settings,
            task_ledger_facts_prompt="custom_task_ledger_facts_prompt",
            task_ledger_plan_prompt="custom_task_ledger_plan_prompt {{$team}}",
        )

        facts, prompt = await manager.create_facts_and_plan(
            ChatHistory(),
            ChatMessageContent(role="user", content="test_message"),
            {"agent_a": "test_agent_a", "agent_b": "test_agent_b"},
        )

        assert isinstance(facts, ChatMessageContent) and facts.content == "mock_response"
        assert isinstance(prompt, ChatMessageContent) and prompt.content == "mock_response"

        assert mock_get_chat_message_content.call_count == 2
        assert (
            mock_get_chat_message_content.call_args_list[0][0][0].messages[0].content
            == "custom_task_ledger_facts_prompt"
        )
        assert (
            mock_get_chat_message_content.call_args_list[1][0][0].messages[2].content
            == "custom_task_ledger_plan_prompt {'agent_a': 'test_agent_a', 'agent_b': 'test_agent_b'}"
        )


async def test_magentic_manager_create_facts_and_prompt_with_old_facts():
    """Test the create_facts_and_prompt method of the MagenticManager with old facts."""

    with patch.object(
        MockChatCompletionService, "get_chat_message_content", new_callable=AsyncMock
    ) as mock_get_chat_message_content:
        mock_get_chat_message_content.return_value = ChatMessageContent(role="assistant", content="mock_response")

        chat_completion_service = MockChatCompletionService(ai_model_id="test")
        prompt_execution_settings = PromptExecutionSettings()

        manager = MagenticManager(
            chat_completion_service=chat_completion_service,
            prompt_execution_settings=prompt_execution_settings,
            task_ledger_facts_update_prompt="custom_task_ledger_facts_prompt {{$old_facts}}",
            task_ledger_plan_update_prompt="custom_task_ledger_plan_prompt {{$team}}",
        )

        facts, prompt = await manager.create_facts_and_plan(
            ChatHistory(),
            ChatMessageContent(role="user", content="test_message"),
            {"agent_a": "test_agent_a", "agent_b": "test_agent_b"},
            old_facts=ChatMessageContent(role="user", content="old_facts"),
        )

        assert isinstance(facts, ChatMessageContent) and facts.content == "mock_response"
        assert isinstance(prompt, ChatMessageContent) and prompt.content == "mock_response"

        assert mock_get_chat_message_content.call_count == 2
        assert (
            mock_get_chat_message_content.call_args_list[0][0][0].messages[0].content
            == "custom_task_ledger_facts_prompt old_facts"
        )
        assert (
            mock_get_chat_message_content.call_args_list[1][0][0].messages[2].content
            == "custom_task_ledger_plan_prompt {'agent_a': 'test_agent_a', 'agent_b': 'test_agent_b'}"
        )


async def test_magentic_manager_create_task_ledger():
    """Test the create_task_ledger method of the MagenticManager."""

    chat_completion_service = MockChatCompletionService(ai_model_id="test")
    prompt_execution_settings = PromptExecutionSettings()

    manager = MagenticManager(
        chat_completion_service=chat_completion_service,
        prompt_execution_settings=prompt_execution_settings,
    )

    task = ChatMessageContent(role="user", content=uuid4().hex)
    facts = ChatMessageContent(role="user", content=uuid4().hex)
    plan = ChatMessageContent(role="user", content=uuid4().hex)
    participants = {"agent_a": "test_agent_a", "agent_b": "test_agent_b"}

    task_ledger = await manager.create_task_ledger(task, facts, plan, participants)

    assert task.content in task_ledger
    assert facts.content in task_ledger
    assert plan.content in task_ledger
    assert "{'agent_a': 'test_agent_a', 'agent_b': 'test_agent_b'}" in task_ledger


async def test_magentic_manager_create_progress_ledger():
    """Test the create_progress_ledger method of the MagenticManager."""

    mock_progress_ledger = ProgressLedger(
        is_request_satisfied=ProgressLedgerItem(answer=False, reason="mock_reasoning"),
        is_in_loop=ProgressLedgerItem(answer=False, reason="mock_reasoning"),
        is_progress_being_made=ProgressLedgerItem(answer=False, reason="mock_reasoning"),
        next_speaker=ProgressLedgerItem(answer="agent_a", reason="mock_reasoning"),
        instruction_or_question=ProgressLedgerItem(answer="mock_instruction", reason="mock_reasoning"),
    )

    task = ChatMessageContent(role="user", content=uuid4().hex)
    participants = {"agent_a": "test_agent_a", "agent_b": "test_agent_b"}

    with patch.object(
        MockChatCompletionService, "get_chat_message_content", new_callable=AsyncMock
    ) as mock_get_chat_message_content:
        mock_get_chat_message_content.return_value = ChatMessageContent(
            role="assistant", content=mock_progress_ledger.model_dump_json()
        )

        chat_completion_service = MockChatCompletionService(ai_model_id="test")
        prompt_execution_settings = PromptExecutionSettings()

        manager = MagenticManager(
            chat_completion_service=chat_completion_service,
            prompt_execution_settings=prompt_execution_settings,
        )

        chat_history = ChatHistory()
        progress_ledger = await manager.create_progress_ledger(chat_history, task, participants)

        assert isinstance(progress_ledger, ProgressLedger)
        assert progress_ledger == mock_progress_ledger

        assert task.content in chat_history.messages[0].content
        assert "{'agent_a': 'test_agent_a', 'agent_b': 'test_agent_b'}" in chat_history.messages[0].content
        assert "agent_a, agent_b" in chat_history.messages[0].content
        assert (
            chat_history.messages[0].content
            == mock_get_chat_message_content.call_args_list[0][0][0].messages[0].content
        )
        assert mock_get_chat_message_content.call_args_list[0][0][1].extension_data["response_format"] == ProgressLedger


# endregion MagenticManager
