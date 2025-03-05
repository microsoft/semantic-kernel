# Copyright (c) Microsoft. All rights reserved.

import pytest
from pydantic import Field, SecretStr, ValidationError

from semantic_kernel.kernel_pydantic import KernelBaseSettings
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class AzureAIAgentSettings(KernelBaseSettings):
    """Slightly modified to ensure invalid data raises ValidationError."""

    env_prefix = "AZURE_AI_AGENT_"
    model_deployment_name: str = Field(min_length=1)
    project_connection_string: SecretStr = Field(..., min_length=1)


def test_azure_ai_agent_settings_valid():
    settings = AzureAIAgentSettings(
        model_deployment_name="test_model",
        project_connection_string="secret_value",
    )
    assert settings.model_deployment_name == "test_model"
    assert settings.project_connection_string.get_secret_value() == "secret_value"


def test_azure_ai_agent_settings_invalid():
    with pytest.raises(ValidationError):
        # Should fail due to min_length=1 constraints
        AzureAIAgentSettings(
            model_deployment_name="",  # empty => invalid
            project_connection_string="",
        )
