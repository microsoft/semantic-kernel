import pytest
from semantic_kernel.connectors.ai.open_ai.models.chat.open_ai_tool_output import (
    OpenAIToolOutput,
)
import yaml
import os
from pydantic import ValidationError

def test_create_instance_valid_data():
    """Test creating an instance with valid data."""
    tool_output = OpenAIToolOutput(tool_call_id="123", output="Some output")
    assert tool_output.tool_call_id == "123"
    assert tool_output.output == "Some output"

def test_create_instance_missing_tool_call_id():
    """Test creating an instance without a tool_call_id."""
    with pytest.raises(ValidationError):
        OpenAIToolOutput(output="Some output")

def test_create_instance_missing_output():
    """Test creating an instance without an output."""
    with pytest.raises(ValidationError):
        OpenAIToolOutput(tool_call_id="123")

def test_create_instance_empty_tool_call_id():
    """Test creating an instance with an empty tool_call_id."""
    with pytest.raises(ValidationError):
        OpenAIToolOutput(tool_call_id="", output="Some output")

def test_create_instance_empty_output():
    """Test creating an instance with an empty output."""
    with pytest.raises(ValidationError):
        OpenAIToolOutput(tool_call_id="123", output="")
