# Copyright (c) Microsoft. All rights reserved.

import pytest
from pydantic import ValidationError

from semantic_kernel.agents.bedrock.bedrock_agent_settings import BedrockAgentSettings


def test_bedrock_agent_settings_from_env_vars(bedrock_agent_unit_test_env):
    """Test loading BedrockAgentSettings from environment variables."""
    settings = BedrockAgentSettings(env_file_path="fake_path")

    assert settings.agent_resource_role_arn == bedrock_agent_unit_test_env["BEDROCK_AGENT_AGENT_RESOURCE_ROLE_ARN"]
    assert settings.foundation_model == bedrock_agent_unit_test_env["BEDROCK_AGENT_FOUNDATION_MODEL"]


@pytest.mark.parametrize(
    "exclude_list",
    [
        ["BEDROCK_AGENT_AGENT_RESOURCE_ROLE_ARN"],
        ["BEDROCK_AGENT_FOUNDATION_MODEL"],
    ],
    indirect=True,
)
def test_bedrock_agent_settings_from_env_vars_missing_required(bedrock_agent_unit_test_env):
    """Test loading BedrockAgentSettings from environment variables with missing required fields."""
    with pytest.raises(ValidationError):
        BedrockAgentSettings(env_file_path="fake_path")
