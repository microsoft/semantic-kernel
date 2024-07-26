# Copyright (c) Microsoft. All rights reserved.


from unittest.mock import patch

import pytest
from pydantic import ValidationError

from semantic_kernel.agents.open_ai.open_ai_service_configuration import (
    AzureOpenAIServiceConfiguration,
    OpenAIServiceConfiguration,
)
from semantic_kernel.exceptions.agent_exceptions import AgentInitializationError


def test_openai_service_configuration_create_success():
    service_id = "test_service"
    ai_model_id = "test_model"
    api_key = "test_key"
    org_id = "test_org"

    config = OpenAIServiceConfiguration.create(
        service_id=service_id,
        ai_model_id=ai_model_id,
        api_key=api_key,
        org_id=org_id,
    )

    assert config.service_id == service_id
    assert config.ai_model_id == ai_model_id
    assert config.api_key == api_key
    assert config.org_id == org_id


@pytest.mark.parametrize("exclude_list", [["OPENAI_API_KEY"]], indirect=True)
def test_openai_service_configuration_create_missing_api_key(openai_unit_test_env):
    with pytest.raises(AgentInitializationError, match="The OpenAI API key is required."):
        OpenAIServiceConfiguration.create(service_id="test_service", env_file_path="test.env")


@pytest.mark.parametrize("exclude_list", [["OPENAI_CHAT_MODEL_ID"]], indirect=True)
def test_openai_service_configuration_create_missing_model_id(openai_unit_test_env):
    with pytest.raises(AgentInitializationError, match="The OpenAI model ID is required."):
        OpenAIServiceConfiguration.create(service_id="test_service", api_key="test_key", env_file_path="test.env")


def test_azure_openai_service_configuration_create_success():
    service_id = "test_service"
    api_key = "test_key"
    endpoint = "https://example.com/"
    deployment_name = "test_deployment"
    api_version = "2021-01-01"

    config = AzureOpenAIServiceConfiguration.create(
        service_id=service_id,
        api_key=api_key,
        endpoint=endpoint,
        deployment_name=deployment_name,
        api_version=api_version,
    )

    assert config.service_id == service_id
    assert config.api_key == api_key
    assert str(config.endpoint) == endpoint
    assert config.deployment_name == deployment_name
    assert config.api_version == api_version


@pytest.mark.parametrize("exclude_list", [["AZURE_OPENAI_CHAT_DEPLOYMENT_NAME"]], indirect=True)
def test_azure_openai_service_configuration_create_missing_deployment_name(azure_openai_unit_test_env):
    with pytest.raises(AgentInitializationError, match="chat_deployment_name is required."):
        AzureOpenAIServiceConfiguration.create(
            service_id="test_service", api_key="test_key", endpoint="https://example.com", env_file_path="test.env"
        )


@pytest.mark.parametrize("exclude_list", [["AZURE_OPENAI_API_KEY"]], indirect=True)
def test_azure_openai_service_configuration_create_missing_authentication(azure_openai_unit_test_env):
    with pytest.raises(AgentInitializationError, match="Please provide either api_key, ad_token or ad_token_provider"):
        AzureOpenAIServiceConfiguration.create(
            service_id="test_service",
            endpoint="https://example.com",
            deployment_name="test_deployment",
            env_file_path="test.env",
        )


def test_open_ai_settings_create_throws(openai_unit_test_env):
    with patch("semantic_kernel.connectors.ai.open_ai.settings.open_ai_settings.OpenAISettings.create") as mock_create:
        mock_create.side_effect = ValidationError.from_exception_data("test", line_errors=[], input_type="python")

        with pytest.raises(AgentInitializationError, match="Failed to create OpenAI settings."):
            OpenAIServiceConfiguration.create(
                service_id="test", api_key="test_api_key", org_id="test_org_id", ai_model_id="test_model_id"
            )


def test_azure_open_ai_settings_create_throws(azure_openai_unit_test_env):
    with patch(
        "semantic_kernel.connectors.ai.open_ai.settings.azure_open_ai_settings.AzureOpenAISettings.create"
    ) as mock_create:
        mock_create.side_effect = ValidationError.from_exception_data("test", line_errors=[], input_type="python")

        with pytest.raises(AgentInitializationError, match="Failed to create Azure OpenAI settings."):
            AzureOpenAIServiceConfiguration.create(
                service_id="test",
                api_key="test_api_key",
                org_id="test_org_id",
            )
