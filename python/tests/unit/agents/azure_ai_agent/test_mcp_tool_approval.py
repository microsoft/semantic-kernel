# Copyright (c) Microsoft. All rights reserved.

import logging
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from azure.ai.agents.models import (
    RequiredMcpToolCall,
    SubmitToolApprovalAction,
    SubmitToolApprovalDetails,
    ThreadRun,
)

from semantic_kernel.agents.azure_ai.agent_thread_actions import AgentThreadActions
from semantic_kernel.agents.azure_ai.azure_ai_agent import AzureAIAgent
from semantic_kernel.agents.azure_ai.mcp_tool_approval import (
    MCPToolApprovalRequest,
)
from semantic_kernel.kernel import Kernel


def _approve_all(request: MCPToolApprovalRequest) -> bool:
    return True


def _mcp_call(call_id: str = "call-1", name: str = "delete_everything") -> MagicMock:
    call = MagicMock(spec=RequiredMcpToolCall)
    call.id = call_id
    call.name = name
    call.arguments = '{"target": "prod"}'
    call.server_label = "attacker_server"
    return call


def _request() -> MCPToolApprovalRequest:
    return MCPToolApprovalRequest(
        agent_name="agentName",
        thread_id="thread-1",
        run_id="run-1",
        tool_call_id="call-1",
        server_label="attacker_server",
        function_name="delete_everything",
        arguments="{}",
    )


# region _resolve_mcp_tool_approval


def _agent(ai_project_client, ai_agent_definition, callback=None) -> AzureAIAgent:
    return AzureAIAgent(
        client=ai_project_client,
        definition=ai_agent_definition,
        mcp_tool_approval_callback=callback,
    )


async def test_resolve_denies_when_no_callback_configured(caplog, ai_project_client, ai_agent_definition):
    agent = _agent(ai_project_client, ai_agent_definition)

    with caplog.at_level(logging.WARNING):
        approved = await AgentThreadActions._resolve_mcp_tool_approval(agent, _request())

    assert approved is False
    assert "mcp_tool_approval_callback" in caplog.text


async def test_resolve_uses_sync_callback(ai_project_client, ai_agent_definition):
    def callback(request: MCPToolApprovalRequest) -> bool:
        assert request.function_name == "delete_everything"
        return True

    agent = _agent(ai_project_client, ai_agent_definition, callback)

    assert await AgentThreadActions._resolve_mcp_tool_approval(agent, _request()) is True


async def test_resolve_uses_async_callback(ai_project_client, ai_agent_definition):
    async def callback(request: MCPToolApprovalRequest) -> bool:
        return False

    agent = _agent(ai_project_client, ai_agent_definition, callback)

    assert await AgentThreadActions._resolve_mcp_tool_approval(agent, _request()) is False


@pytest.mark.parametrize("value", [True, False])
async def test_resolve_returns_callback_decision(value: bool, ai_project_client, ai_agent_definition):
    agent = _agent(ai_project_client, ai_agent_definition, lambda request: value)

    assert await AgentThreadActions._resolve_mcp_tool_approval(agent, _request()) is value


async def test_resolve_denies_when_callback_raises(ai_project_client, ai_agent_definition):
    def callback(request: MCPToolApprovalRequest) -> bool:
        raise RuntimeError("boom")

    agent = _agent(ai_project_client, ai_agent_definition, callback)

    assert await AgentThreadActions._resolve_mcp_tool_approval(agent, _request()) is False


async def test_resolve_denies_on_non_true_return_value(ai_project_client, ai_agent_definition):
    agent = _agent(ai_project_client, ai_agent_definition, lambda request: "yes please")
    assert await AgentThreadActions._resolve_mcp_tool_approval(agent, _request()) is False

    agent = _agent(ai_project_client, ai_agent_definition, lambda request: None)
    assert await AgentThreadActions._resolve_mcp_tool_approval(agent, _request()) is False


# region _build_mcp_tool_approvals


async def test_build_approvals_denies_by_default(ai_project_client, ai_agent_definition):
    agent = AzureAIAgent(client=ai_project_client, definition=ai_agent_definition)

    approvals = await AgentThreadActions._build_mcp_tool_approvals(
        agent=agent,
        thread_id="thread-1",
        run_id="run-1",
        mcp_tool_calls=[_mcp_call()],
    )

    assert len(approvals) == 1
    assert approvals[0].approve is False
    assert approvals[0].tool_call_id == "call-1"


async def test_build_approvals_uses_agent_callback(ai_project_client, ai_agent_definition):
    seen: list[MCPToolApprovalRequest] = []

    def callback(request: MCPToolApprovalRequest) -> bool:
        seen.append(request)
        return True

    agent = AzureAIAgent(
        client=ai_project_client,
        definition=ai_agent_definition,
        mcp_tool_approval_callback=callback,
    )

    approvals = await AgentThreadActions._build_mcp_tool_approvals(
        agent=agent,
        thread_id="thread-1",
        run_id="run-1",
        mcp_tool_calls=[_mcp_call()],
    )

    assert approvals[0].approve is True
    assert seen[0].agent_name == "agentName"
    assert seen[0].thread_id == "thread-1"
    assert seen[0].run_id == "run-1"
    assert seen[0].server_label == "attacker_server"
    assert seen[0].function_name == "delete_everything"
    assert seen[0].arguments == '{"target": "prod"}'


async def test_build_approvals_denies_when_callback_returns_false(ai_project_client, ai_agent_definition):
    agent = AzureAIAgent(
        client=ai_project_client,
        definition=ai_agent_definition,
        mcp_tool_approval_callback=lambda request: False,
    )

    approvals = await AgentThreadActions._build_mcp_tool_approvals(
        agent=agent,
        thread_id="thread-1",
        run_id="run-1",
        mcp_tool_calls=[_mcp_call()],
    )

    assert approvals[0].approve is False


async def test_build_approvals_decides_per_call(ai_project_client, ai_agent_definition):
    def callback(request: MCPToolApprovalRequest) -> bool:
        return request.function_name == "safe_tool"

    agent = AzureAIAgent(
        client=ai_project_client,
        definition=ai_agent_definition,
        mcp_tool_approval_callback=callback,
    )

    approvals = await AgentThreadActions._build_mcp_tool_approvals(
        agent=agent,
        thread_id="thread-1",
        run_id="run-1",
        mcp_tool_calls=[_mcp_call("call-1", "safe_tool"), _mcp_call("call-2", "delete_everything")],
    )

    assert [(a.tool_call_id, a.approve) for a in approvals] == [("call-1", True), ("call-2", False)]


# region end-to-end invoke


async def _run_invoke_with_pending_mcp_call(agent) -> AsyncMock:
    """Drive AgentThreadActions.invoke through a single SubmitToolApprovalAction and return the submit mock."""
    run = ThreadRun(
        id="run123",
        thread_id="thread123",
        status="running",
        instructions="test agent",
        created_at=int(datetime.now(timezone.utc).timestamp()),
        model="model",
    )

    agent.client.agents = MagicMock()
    agent.client.agents.runs = MagicMock()
    agent.client.agents.runs.create = AsyncMock(return_value=run)
    agent.client.agents.runs.submit_tool_outputs = AsyncMock()

    async def mock_list_run_steps(*args, **kwargs):
        return
        yield  # pragma: no cover - makes this an async generator

    agent.client.agents.run_steps = MagicMock()
    agent.client.agents.run_steps.list = mock_list_run_steps

    poll_count = 0

    async def mock_poll_run_status(*args, **kwargs):
        nonlocal poll_count
        if poll_count == 0:
            run.status = "requires_action"
            run.required_action = SubmitToolApprovalAction(
                submit_tool_approval=SubmitToolApprovalDetails(tool_calls=[_mcp_call()])
            )
        else:
            run.status = "completed"
        poll_count += 1
        return run

    with patch.object(AgentThreadActions, "_poll_run_status", side_effect=mock_poll_run_status):
        async for _ in AgentThreadActions.invoke(
            agent=agent,
            thread_id="thread123",
            kernel=AsyncMock(spec=Kernel),
        ):
            pass

    return agent.client.agents.runs.submit_tool_outputs


async def test_invoke_denies_mcp_call_without_callback(ai_project_client, ai_agent_definition):
    agent = AzureAIAgent(client=ai_project_client, definition=ai_agent_definition)

    submit_tool_outputs = await _run_invoke_with_pending_mcp_call(agent)

    submit_tool_outputs.assert_awaited_once()
    approvals = submit_tool_outputs.await_args.kwargs["tool_approvals"]
    assert [a.approve for a in approvals] == [False]


async def test_invoke_approves_mcp_call_with_callback(ai_project_client, ai_agent_definition):
    agent = AzureAIAgent(
        client=ai_project_client,
        definition=ai_agent_definition,
        mcp_tool_approval_callback=_approve_all,
    )

    submit_tool_outputs = await _run_invoke_with_pending_mcp_call(agent)

    submit_tool_outputs.assert_awaited_once()
    approvals = submit_tool_outputs.await_args.kwargs["tool_approvals"]
    assert [a.approve for a in approvals] == [True]
