# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.agents.bedrock.models.bedrock_agent_model import BedrockAgentModel


def test_bedrock_agent_model_valid():
    """Test case to verify the BedrockAgentModel with valid data."""
    model = BedrockAgentModel(
        agentId="test_id",
        agentName="test_name",
        agentVersion="1.0",
        foundationModel="test_model",
        agentStatus="CREATING",
    )
    assert model.agent_id == "test_id"
    assert model.agent_name == "test_name"
    assert model.agent_version == "1.0"
    assert model.foundation_model == "test_model"
    assert model.agent_status == "CREATING"


def test_bedrock_agent_model_missing_agent_id():
    """Test case to verify the BedrockAgentModel with missing agentId."""
    model = BedrockAgentModel(
        agentName="test_name",
        agentVersion="1.0",
        foundationModel="test_model",
        agentStatus="CREATING",
    )
    assert model.agent_id is None
    assert model.agent_name == "test_name"
    assert model.agent_version == "1.0"
    assert model.foundation_model == "test_model"
    assert model.agent_status == "CREATING"


def test_bedrock_agent_model_missing_agent_name():
    """Test case to verify the BedrockAgentModel with missing agentName."""
    model = BedrockAgentModel(
        agentId="test_id",
        agentVersion="1.0",
        foundationModel="test_model",
        agentStatus="CREATING",
    )
    assert model.agent_id == "test_id"
    assert model.agent_name is None
    assert model.agent_version == "1.0"
    assert model.foundation_model == "test_model"
    assert model.agent_status == "CREATING"


def test_bedrock_agent_model_extra_field():
    """Test case to verify the BedrockAgentModel with an extra field."""
    model = BedrockAgentModel(
        agentId="test_id",
        agentName="test_name",
        agentVersion="1.0",
        foundationModel="test_model",
        agentStatus="CREATING",
        extraField="extra_value",
    )
    assert model.agent_id == "test_id"
    assert model.agent_name == "test_name"
    assert model.agent_version == "1.0"
    assert model.foundation_model == "test_model"
    assert model.agent_status == "CREATING"
    assert model.extraField == "extra_value"
