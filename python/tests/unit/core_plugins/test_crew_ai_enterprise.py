# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import patch

import pytest

from semantic_kernel.core_plugins.crew_ai.crew_ai_enterprise import CrewAIEnterprise
from semantic_kernel.core_plugins.crew_ai.crew_ai_models import CrewAIEnterpriseKickoffState, CrewAIStatusResponse
from semantic_kernel.exceptions.function_exceptions import PluginInitializationError
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata
from semantic_kernel.functions.kernel_plugin import KernelPlugin


@pytest.fixture
def crew_ai_enterprise():
    return CrewAIEnterprise(endpoint="https://test.com", auth_token="FakeToken")


def test_it_can_be_instantiated(crew_ai_enterprise):
    assert crew_ai_enterprise is not None


def test_create_kernel_plugin(crew_ai_enterprise):
    plugin = crew_ai_enterprise.create_kernel_plugin(
        name="test_plugin",
        description="Test plugin",
        parameters=[KernelParameterMetadata(name="param1")],
    )
    assert isinstance(plugin, KernelPlugin)
    assert "kickoff" in plugin.functions
    assert "kickoff_and_wait" in plugin.functions
    assert "get_status" in plugin.functions
    assert "wait_for_completion" in plugin.functions


@patch("semantic_kernel.core_plugins.crew_ai.crew_ai_enterprise.CrewAIEnterpriseClient.kickoff")
async def test_kickoff(mock_kickoff, crew_ai_enterprise):
    mock_kickoff.return_value.kickoff_id = "123"
    kickoff_id = await crew_ai_enterprise.kickoff(inputs={"param1": "value"})
    assert kickoff_id == "123"


@pytest.mark.parametrize(
    "state",
    [
        CrewAIEnterpriseKickoffState.Pending,
        CrewAIEnterpriseKickoffState.Started,
        CrewAIEnterpriseKickoffState.Running,
        CrewAIEnterpriseKickoffState.Success,
        CrewAIEnterpriseKickoffState.Failed,
        CrewAIEnterpriseKickoffState.Failure,
        CrewAIEnterpriseKickoffState.Not_Found,
    ],
)
@patch("semantic_kernel.core_plugins.crew_ai.crew_ai_enterprise.CrewAIEnterpriseClient.get_status")
async def test_get_crew_kickoff_status(mock_get_status, crew_ai_enterprise, state):
    mock_get_status.return_value = CrewAIStatusResponse(state=state.value)
    status_response = await crew_ai_enterprise.get_crew_kickoff_status(kickoff_id="123")
    assert status_response.state == state


@patch("semantic_kernel.core_plugins.crew_ai.crew_ai_enterprise.CrewAIEnterpriseClient.get_status")
async def test_wait_for_crew_completion(mock_get_status, crew_ai_enterprise):
    mock_get_status.side_effect = [
        CrewAIStatusResponse(state=CrewAIEnterpriseKickoffState.Pending),
        CrewAIStatusResponse(state=CrewAIEnterpriseKickoffState.Success, result="result"),
    ]
    result = await crew_ai_enterprise.wait_for_crew_completion(kickoff_id="123")
    assert result == "result"


def test_build_arguments(crew_ai_enterprise):
    parameters = [KernelParameterMetadata(name="param1")]
    arguments = {"param1": "value"}
    args = crew_ai_enterprise._build_arguments(parameters, arguments)
    assert args["param1"] == "value"


def test_build_arguments_missing_param(crew_ai_enterprise):
    parameters = [KernelParameterMetadata(name="param1")]
    arguments = {}
    with pytest.raises(PluginInitializationError):
        crew_ai_enterprise._build_arguments(parameters, arguments)


@patch("semantic_kernel.core_plugins.crew_ai.crew_ai_enterprise.CrewAIEnterpriseClient.__aenter__")
async def test_aenter(mock_aenter, crew_ai_enterprise):
    await crew_ai_enterprise.__aenter__()
    mock_aenter.assert_called_once()


@patch("semantic_kernel.core_plugins.crew_ai.crew_ai_enterprise.CrewAIEnterpriseClient.__aexit__")
async def test_aexit(mock_aexit, crew_ai_enterprise):
    await crew_ai_enterprise.__aexit__()
    mock_aexit.assert_called_once()
