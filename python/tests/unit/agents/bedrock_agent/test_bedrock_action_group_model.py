# Copyright (c) Microsoft. All rights reserved.

import pytest
from pydantic import ValidationError

from semantic_kernel.agents.bedrock.models.bedrock_action_group_model import BedrockActionGroupModel


def test_bedrock_action_group_model_valid():
    """Test case to verify the BedrockActionGroupModel with valid data."""
    model = BedrockActionGroupModel(actionGroupId="test_id", actionGroupName="test_name")
    assert model.action_group_id == "test_id"
    assert model.action_group_name == "test_name"


def test_bedrock_action_group_model_missing_action_group_id():
    """Test case to verify error handling when actionGroupId is missing."""
    with pytest.raises(ValidationError):
        BedrockActionGroupModel(actionGroupName="test_name")


def test_bedrock_action_group_model_missing_action_group_name():
    """Test case to verify error handling when actionGroupName is missing."""
    with pytest.raises(ValidationError):
        BedrockActionGroupModel(actionGroupId="test_id")


def test_bedrock_action_group_model_extra_field():
    """Test case to verify the BedrockActionGroupModel with an extra field."""
    model = BedrockActionGroupModel(actionGroupId="test_id", actionGroupName="test_name", extraField="extra_value")
    assert model.action_group_id == "test_id"
    assert model.action_group_name == "test_name"
    assert model.extraField == "extra_value"
