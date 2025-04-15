# Copyright (c) Microsoft. All rights reserved.

from collections.abc import Callable

import pytest

from semantic_kernel.agents.bedrock.models.bedrock_agent_event_type import BedrockAgentEventType
from semantic_kernel.agents.bedrock.models.bedrock_agent_model import BedrockAgentModel
from semantic_kernel.agents.bedrock.models.bedrock_agent_status import BedrockAgentStatus
from semantic_kernel.kernel import Kernel


@pytest.fixture()
def bedrock_agent_unit_test_env(monkeypatch, exclude_list, override_env_param_dict):
    """Fixture to set environment variables for Amazon Bedrock Agent unit tests."""
    if exclude_list is None:
        exclude_list = []

    if override_env_param_dict is None:
        override_env_param_dict = {}

    env_vars = {
        "BEDROCK_AGENT_AGENT_RESOURCE_ROLE_ARN": "TEST_BEDROCK_AGENT_AGENT_RESOURCE_ROLE_ARN",
        "BEDROCK_AGENT_FOUNDATION_MODEL": "TEST_BEDROCK_AGENT_FOUNDATION_MODEL",
    }

    env_vars.update(override_env_param_dict)

    for key, value in env_vars.items():
        if key not in exclude_list:
            monkeypatch.setenv(key, value)
        else:
            monkeypatch.delenv(key, raising=False)

    return env_vars


@pytest.fixture
def kernel_with_function(kernel: Kernel, decorated_native_function: Callable) -> Kernel:
    kernel.add_function("test_plugin", function=decorated_native_function)

    return kernel


@pytest.fixture
def new_agent_name():
    return "test_agent_name"


@pytest.fixture
def bedrock_agent_model():
    return BedrockAgentModel(
        agent_name="test_agent_name",
        foundation_model="test_foundation_model",
        agent_status=BedrockAgentStatus.NOT_PREPARED,
    )


@pytest.fixture
def bedrock_agent_model_with_id():
    return BedrockAgentModel(
        agent_id="test_agent_id",
        agent_name="test_agent_name",
        foundation_model="test_foundation_model",
        agent_status=BedrockAgentStatus.NOT_PREPARED,
    )


@pytest.fixture
def bedrock_agent_model_with_id_prepared_dict():
    return {
        "agent": {
            "agentId": "test_agent_id",
            "agentName": "test_agent_name",
            "foundationModel": "test_foundation_model",
            "agentStatus": "PREPARED",
        }
    }


@pytest.fixture
def bedrock_agent_model_with_id_preparing_dict():
    return {
        "agent": {
            "agentId": "test_agent_id",
            "agentName": "test_agent_name",
            "foundationModel": "test_foundation_model",
            "agentStatus": "PREPARING",
        }
    }


@pytest.fixture
def bedrock_agent_model_with_id_not_prepared_dict():
    return {
        "agent": {
            "agentId": "test_agent_id",
            "agentName": "test_agent_name",
            "foundationModel": "test_foundation_model",
            "agentStatus": "NOT_PREPARED",
        }
    }


@pytest.fixture
def existing_agent_not_prepared_model():
    return BedrockAgentModel(
        agent_id="test_agent_id",
        agent_name="test_agent_name",
        foundation_model="test_foundation_model",
        agent_status=BedrockAgentStatus.NOT_PREPARED,
    )


@pytest.fixture
def bedrock_action_group_mode_dict():
    return {
        "agentActionGroup": {
            "actionGroupId": "test_action_group_id",
            "actionGroupName": "test_action_group_name",
        }
    }


@pytest.fixture
def simple_response():
    return "test response"


@pytest.fixture
def bedrock_agent_non_streaming_empty_response():
    return {
        "completion": [],
    }


@pytest.fixture
def bedrock_agent_non_streaming_simple_response(simple_response):
    return {
        "completion": [
            {
                "chunk": {"bytes": bytes(simple_response, "utf-8")},
            },
        ],
    }


@pytest.fixture
def bedrock_agent_streaming_simple_response(simple_response):
    return {
        "completion": [
            {
                "chunk": {"bytes": bytes(chunk, "utf-8")},
            }
            for chunk in simple_response
        ]
    }


@pytest.fixture
def bedrock_agent_function_call_response():
    return {
        "completion": [
            {
                BedrockAgentEventType.RETURN_CONTROL: {
                    "invocationId": "test_invocation_id",
                    "invocationInputs": [
                        {
                            "functionInvocationInput": {
                                "function": "test_function",
                                "parameters": [
                                    {"name": "test_parameter_name", "value": "test_parameter_value"},
                                ],
                            },
                        },
                    ],
                },
            },
        ],
    }


@pytest.fixture
def bedrock_agent_create_session_response():
    return {
        "sessionId": "test_session_id",
    }
