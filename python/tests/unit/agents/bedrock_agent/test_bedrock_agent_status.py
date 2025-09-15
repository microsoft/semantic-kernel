# Copyright (c) Microsoft. All rights reserved.

import pytest

from semantic_kernel.agents.bedrock.models.bedrock_agent_status import BedrockAgentStatus


def test_bedrock_agent_status_values():
    """Test case to verify the values of BedrockAgentStatus enum."""
    assert BedrockAgentStatus.CREATING == "CREATING"
    assert BedrockAgentStatus.PREPARING == "PREPARING"
    assert BedrockAgentStatus.PREPARED == "PREPARED"
    assert BedrockAgentStatus.NOT_PREPARED == "NOT_PREPARED"
    assert BedrockAgentStatus.DELETING == "DELETING"
    assert BedrockAgentStatus.FAILED == "FAILED"
    assert BedrockAgentStatus.VERSIONING == "VERSIONING"
    assert BedrockAgentStatus.UPDATING == "UPDATING"


def test_bedrock_agent_status_invalid_value():
    """Test case to verify error handling for invalid BedrockAgentStatus value."""
    with pytest.raises(ValueError):
        BedrockAgentStatus("INVALID_STATUS")
