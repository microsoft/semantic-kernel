# Copyright (c) Microsoft. All rights reserved.

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from semantic_kernel.agents.bedrock.bedrock_agent_settings import BedrockAgentSettings


def test_bedrock_agent_settings_from_env_vars():
    """Test loading BedrockAgentSettings from environment variables."""
    with patch.dict(os.environ, {"BEDROCK_AGENT_AGENT_RESOURCE_ROLE_ARN": "test_arn", "BEDROCK_AGENT_FOUNDATION_MODEL": "test_model"}):
        settings = BedrockAgentSettings()
        assert settings.agent_resource_role_arn == "test_arn"
        assert settings.foundation_model == "test_model"


def test_bedrock_agent_settings_from_env_vars_missing_optional():
    """Test loading BedrockAgentSettings from environment variables with missing optional fields."""
    with patch.dict(os.environ, {"BEDROCK_AGENT_AGENT_RESOURCE_ROLE_ARN": "test_arn"}):
        settings = BedrockAgentSettings()
        assert settings.agent_resource_role_arn == "test_arn"
        assert settings.foundation_model is None


def test_bedrock_agent_settings_from_env_vars_missing_required():
    """Test loading BedrockAgentSettings from environment variables with missing required fields."""
    with patch.dict(os.environ, {"BEDROCK_AGENT_FOUNDATION_MODEL": "test_model"}):
        with pytest.raises(ValidationError):
            BedrockAgentSettings()


def test_bedrock_agent_settings_from_dotenv_file(tmp_path):
    """Test loading BedrockAgentSettings from a .env file."""
    dotenv_file = tmp_path / ".env"
    dotenv_file.write_text("BEDROCK_AGENT_AGENT_RESOURCE_ROLE_ARN=test_arn\nBEDROCK_AGENT_FOUNDATION_MODEL=test_model\n")

    with patch("semantic_kernel.agents.bedrock.bedrock_agent_settings.BedrockAgentSettings.__config__.env_file", dotenv_file):
        settings = BedrockAgentSettings()
        assert settings.agent_resource_role_arn == "test_arn"
        assert settings.foundation_model == "test_model"


def test_bedrock_agent_settings_from_dotenv_file_missing_optional(tmp_path):
    """Test loading BedrockAgentSettings from a .env file with missing optional fields."""
    dotenv_file = tmp_path / ".env"
    dotenv_file.write_text("BEDROCK_AGENT_AGENT_RESOURCE_ROLE_ARN=test_arn\n")

    with patch("semantic_kernel.agents.bedrock.bedrock_agent_settings.BedrockAgentSettings.__config__.env_file", dotenv_file):
        settings = BedrockAgentSettings()
        assert settings.agent_resource_role_arn == "test_arn"
        assert settings.foundation_model is None


def test_bedrock_agent_settings_from_dotenv_file_missing_required(tmp_path):
    """Test loading BedrockAgentSettings from a .env file with missing required fields."""
    dotenv_file = tmp_path / ".env"
    dotenv_file.write_text("BEDROCK_AGENT_FOUNDATION_MODEL=test_model\n")

    with patch("semantic_kernel.agents.bedrock.bedrock_agent_settings.BedrockAgentSettings.__config__.env_file", dotenv_file):
        with pytest.raises(ValidationError):
            BedrockAgentSettings()
