import pytest
import yaml
from pydantic import ValidationError

from semantic_kernel.connectors.ai.open_ai.models.chat.open_ai_assistant_settings import (
    OpenAIAssistantSettings,
)


# Fixture for valid data
@pytest.fixture
def valid_data():
    return {
        "name": "Test Assistant",
        "description": "A test description.",
        "instructions": "Some instructions.",
    }


# Fixture for creating a temporary YAML file
@pytest.fixture
def temp_yaml_file(tmp_path, valid_data):
    d = tmp_path / "sub"
    d.mkdir()
    p = d / "settings.yaml"
    with open(p, "w") as file:
        yaml.dump(valid_data, file)
    return p


def test_create_instance_valid_data(valid_data):
    """Test creating an instance with valid data."""
    assistant = OpenAIAssistantSettings(**valid_data)
    assert assistant.name == valid_data["name"]
    assert assistant.description == valid_data["description"]
    assert assistant.instructions == valid_data["instructions"]


def test_create_instance_invalid_data():
    """Test creating an instance with invalid data."""
    with pytest.raises(ValidationError):
        OpenAIAssistantSettings(name="", description="A test description.")


def test_load_from_definition_file_valid(temp_yaml_file):
    """Test loading settings from a valid YAML file."""
    assistant = OpenAIAssistantSettings.load_from_definition_file(str(temp_yaml_file))
    assert assistant.name == "Test Assistant"
    assert assistant.description == "A test description."
    assert assistant.instructions == "Some instructions."


def test_load_from_definition_file_invalid():
    """Test loading settings from an invalid (non-existing) file."""
    with pytest.raises(FileNotFoundError):
        OpenAIAssistantSettings.load_from_definition_file("non_existing_file.yaml")
