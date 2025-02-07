# Copyright (c) Microsoft. All rights reserved.


from unittest.mock import AsyncMock

import pytest
from crew_ai.crew_ai_enterprise import CrewAIEnterprise
from crew_ai.crew_ai_models import InputMetadata


@pytest.fixture
def mock_client():
    return AsyncMock()


@pytest.fixture
def auth_token_provider():
    return AsyncMock(return_value="fake_token")


@pytest.fixture
def crew_ai_enterprise(mock_client, auth_token_provider):
    crew_ai = CrewAIEnterprise(endpoint="http://fake-endpoint", auth_token_provider=auth_token_provider)
    crew_ai._crew_client = mock_client
    return crew_ai


@pytest.mark.asyncio
async def test_kickoff_async(crew_ai_enterprise, mock_client):
    mock_client.kickoff_async.return_value = AsyncMock(kickoff_id="12345")
    kickoff_id = await crew_ai_enterprise.kickoff_async(inputs={"key": "value"})
    assert kickoff_id == "12345"
    mock_client.kickoff_async.assert_called_once_with({"key": "value"}, None, None, None)


@pytest.mark.asyncio
async def test_get_crew_kickoff_status_async(crew_ai_enterprise, mock_client):
    mock_client.get_status_async.return_value = AsyncMock(state="Success")
    status_response = await crew_ai_enterprise.get_crew_kickoff_status_async("12345")
    assert status_response.state == "Success"
    mock_client.get_status_async.assert_called_once_with("12345")


@pytest.mark.asyncio
async def test_wait_for_crew_completion_async(crew_ai_enterprise, mock_client):
    mock_client.get_status_async.side_effect = [
        AsyncMock(state="Pending"),
        AsyncMock(state="Pending"),
        AsyncMock(state="Success", result="Completed"),
    ]
    result = await crew_ai_enterprise.wait_for_crew_completion_async("12345")
    assert result == "Completed"
    assert mock_client.get_status_async.call_count == 3


def test_create_kernel_plugin(crew_ai_enterprise):
    plugin = crew_ai_enterprise.create_kernel_plugin(
        name="test_plugin", description="Test Plugin", input_metadata=[InputMetadata(name="input1", type="string")]
    )
    assert plugin.name == "test_plugin"
    assert plugin.description == "Test Plugin"


def test_build_arguments(crew_ai_enterprise):
    input_metadata = [InputMetadata(name="input1", type="string")]
    arguments = {"input1": "value1"}
    args = crew_ai_enterprise._build_arguments(input_metadata, arguments)
    assert args == {"input1": "value1"}


def test_build_arguments_missing_input(crew_ai_enterprise):
    input_metadata = [InputMetadata(name="input1", type="string")]
    arguments = {}
    with pytest.raises(Exception, match="Missing required input 'input1' for CrewAI."):
        crew_ai_enterprise._build_arguments(input_metadata, arguments)
