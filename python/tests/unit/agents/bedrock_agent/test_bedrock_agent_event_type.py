# Copyright (c) Microsoft. All rights reserved.

import pytest

from semantic_kernel.agents.bedrock.models.bedrock_agent_event_type import BedrockAgentEventType


def test_bedrock_agent_event_type_values():
    """Test case to verify the values of BedrockAgentEventType enum."""
    assert BedrockAgentEventType.CHUNK.value == "chunk"
    assert BedrockAgentEventType.TRACE.value == "trace"
    assert BedrockAgentEventType.RETURN_CONTROL.value == "returnControl"
    assert BedrockAgentEventType.FILES.value == "files"


def test_bedrock_agent_event_type_enum():
    """Test case to verify the type of BedrockAgentEventType enum members."""
    assert isinstance(BedrockAgentEventType.CHUNK, BedrockAgentEventType)
    assert isinstance(BedrockAgentEventType.TRACE, BedrockAgentEventType)
    assert isinstance(BedrockAgentEventType.RETURN_CONTROL, BedrockAgentEventType)
    assert isinstance(BedrockAgentEventType.FILES, BedrockAgentEventType)


def test_bedrock_agent_event_type_invalid():
    """Test case to verify error handling for invalid BedrockAgentEventType value."""
    with pytest.raises(ValueError):
        BedrockAgentEventType("invalid_value")
