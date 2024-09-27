# Copyright (c) Microsoft. All rights reserved.

import pytest
from pydantic import ValidationError

from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.azure_chat_prompt_execution_settings import (
    AzureAISearchDataSources,
    AzureChatPromptExecutionSettings,
    AzureDataSources,
    ExtraBody,
)
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIChatPromptExecutionSettings,
    OpenAITextPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings


def test_default_openai_chat_prompt_execution_settings():
    settings = OpenAIChatPromptExecutionSettings()
    assert settings.temperature == 0.0
    assert settings.top_p == 1.0
    assert settings.presence_penalty == 0.0
    assert settings.frequency_penalty == 0.0
    assert settings.max_tokens == 256
    assert settings.stop is None
    assert settings.number_of_responses == 1
    assert settings.logit_bias == {}
    assert settings.messages is None


def test_custom_openai_chat_prompt_execution_settings():
    settings = OpenAIChatPromptExecutionSettings(
        temperature=0.5,
        top_p=0.5,
        presence_penalty=0.5,
        frequency_penalty=0.5,
        max_tokens=128,
        stop="\n",
        number_of_responses=2,
        logit_bias={"1": 1},
        messages=[{"role": "system", "content": "Hello"}],
    )
    assert settings.temperature == 0.5
    assert settings.top_p == 0.5
    assert settings.presence_penalty == 0.5
    assert settings.frequency_penalty == 0.5
    assert settings.max_tokens == 128
    assert settings.stop == "\n"
    assert settings.number_of_responses == 2
    assert settings.logit_bias == {"1": 1}
    assert settings.messages == [{"role": "system", "content": "Hello"}]


def test_openai_chat_prompt_execution_settings_from_default_completion_config():
    settings = PromptExecutionSettings(service_id="test_service")
    chat_settings = OpenAIChatPromptExecutionSettings.from_prompt_execution_settings(settings)
    assert chat_settings.service_id == "test_service"
    assert chat_settings.temperature == 0.0
    assert chat_settings.top_p == 1.0
    assert chat_settings.presence_penalty == 0.0
    assert chat_settings.frequency_penalty == 0.0
    assert chat_settings.max_tokens == 256
    assert chat_settings.stop is None
    assert chat_settings.number_of_responses == 1
    assert chat_settings.logit_bias == {}


def test_openai_chat_prompt_execution_settings_from_openai_prompt_execution_settings():
    chat_settings = OpenAIChatPromptExecutionSettings(service_id="test_service", temperature=1.0)
    new_settings = OpenAIChatPromptExecutionSettings(service_id="test_2", temperature=0.0)
    chat_settings.update_from_prompt_execution_settings(new_settings)
    assert chat_settings.service_id == "test_2"
    assert chat_settings.temperature == 0.0


def test_openai_text_prompt_execution_settings_validation():
    with pytest.raises(ValidationError, match="best_of must be greater than number_of_responses"):
        OpenAITextPromptExecutionSettings(best_of=1, number_of_responses=2)


def test_openai_text_prompt_execution_settings_validation_manual():
    text_oai = OpenAITextPromptExecutionSettings(best_of=1, number_of_responses=1)
    with pytest.raises(ValidationError, match="best_of must be greater than number_of_responses"):
        text_oai.number_of_responses = 2


def test_openai_chat_prompt_execution_settings_from_custom_completion_config():
    settings = PromptExecutionSettings(
        service_id="test_service",
        extension_data={
            "temperature": 0.5,
            "top_p": 0.5,
            "presence_penalty": 0.5,
            "frequency_penalty": 0.5,
            "max_tokens": 128,
            "stop": ["\n"],
            "number_of_responses": 2,
            "logprobs": 1,
            "logit_bias": {"1": 1},
            "messages": [{"role": "system", "content": "Hello"}],
        },
    )
    chat_settings = OpenAIChatPromptExecutionSettings.from_prompt_execution_settings(settings)
    assert chat_settings.temperature == 0.5
    assert chat_settings.top_p == 0.5
    assert chat_settings.presence_penalty == 0.5
    assert chat_settings.frequency_penalty == 0.5
    assert chat_settings.max_tokens == 128
    assert chat_settings.stop == ["\n"]
    assert chat_settings.number_of_responses == 2
    assert chat_settings.logit_bias == {"1": 1}


def test_openai_chat_prompt_execution_settings_from_custom_completion_config_with_none():
    settings = PromptExecutionSettings(
        service_id="test_service",
        extension_data={
            "temperature": 0.5,
            "top_p": 0.5,
            "presence_penalty": 0.5,
            "frequency_penalty": 0.5,
            "max_tokens": 128,
            "stop": ["\n"],
            "number_of_responses": 2,
            "functions": None,
            "logit_bias": {"1": 1},
            "messages": [{"role": "system", "content": "Hello"}],
        },
    )
    chat_settings = OpenAIChatPromptExecutionSettings.from_prompt_execution_settings(settings)
    assert chat_settings.temperature == 0.5
    assert chat_settings.top_p == 0.5
    assert chat_settings.presence_penalty == 0.5
    assert chat_settings.frequency_penalty == 0.5
    assert chat_settings.max_tokens == 128
    assert chat_settings.stop == ["\n"]
    assert chat_settings.number_of_responses == 2
    assert chat_settings.logit_bias == {"1": 1}
    assert chat_settings.functions is None


def test_openai_chat_prompt_execution_settings_from_custom_completion_config_with_functions():
    settings = PromptExecutionSettings(
        service_id="test_service",
        extension_data={
            "temperature": 0.5,
            "top_p": 0.5,
            "presence_penalty": 0.5,
            "frequency_penalty": 0.5,
            "max_tokens": 128,
            "stop": ["\n"],
            "number_of_responses": 2,
            "functions": [{}],
            "function_call": "auto",
            "logit_bias": {"1": 1},
            "messages": [{"role": "system", "content": "Hello"}],
        },
    )
    chat_settings = OpenAIChatPromptExecutionSettings.from_prompt_execution_settings(settings)
    assert chat_settings.temperature == 0.5
    assert chat_settings.top_p == 0.5
    assert chat_settings.presence_penalty == 0.5
    assert chat_settings.frequency_penalty == 0.5
    assert chat_settings.max_tokens == 128
    assert chat_settings.stop == ["\n"]
    assert chat_settings.number_of_responses == 2
    assert chat_settings.logit_bias == {"1": 1}
    assert chat_settings.functions == [{}]


def test_create_options():
    settings = OpenAIChatPromptExecutionSettings(
        temperature=0.5,
        top_p=0.5,
        presence_penalty=0.5,
        frequency_penalty=0.5,
        max_tokens=128,
        stop=["\n"],
        number_of_responses=2,
        logit_bias={"1": 1},
        messages=[{"role": "system", "content": "Hello"}],
        function_call="auto",
    )
    options = settings.prepare_settings_dict()
    assert options["temperature"] == 0.5
    assert options["top_p"] == 0.5
    assert options["presence_penalty"] == 0.5
    assert options["frequency_penalty"] == 0.5
    assert options["max_tokens"] == 128
    assert options["stop"] == ["\n"]
    assert options["n"] == 2
    assert options["logit_bias"] == {"1": 1}
    assert not options["stream"]


def test_create_options_azure_data():
    az_source = AzureAISearchDataSources(indexName="test-index", endpoint="test-endpoint", key="test-key")
    az_data = AzureDataSources(type="AzureCognitiveSearch", parameters=az_source)
    extra = ExtraBody(dataSources=[az_data])
    settings = AzureChatPromptExecutionSettings(extra_body=extra)
    options = settings.prepare_settings_dict()
    assert options["extra_body"] == extra.model_dump(exclude_none=True, by_alias=True)


def test_azure_open_ai_chat_prompt_execution_settings_with_cosmosdb_data_sources():  # noqa: E501
    input_dict = {
        "messages": [{"role": "system", "content": "Hello"}],
        "extra_body": {
            "dataSources": [
                {
                    "type": "AzureCosmosDB",
                    "parameters": {
                        "authentication": {
                            "type": "ConnectionString",
                            "connectionString": "mongodb+srv://onyourdatatest:{password}$@{cluster-name}.mongocluster.cosmos.azure.com/?tls=true&authMechanism=SCRAM-SHA-256&retrywrites=false&maxIdleTimeMS=120000",
                        },
                        "databaseName": "vectordb",
                        "containerName": "azuredocs",
                        "indexName": "azuredocindex",
                        "embeddingDependency": {
                            "type": "DeploymentName",
                            "deploymentName": "{embedding deployment name}",
                        },
                        "fieldsMapping": {"vectorFields": ["contentvector"]},
                    },
                }
            ]
        },
    }
    settings = AzureChatPromptExecutionSettings.model_validate(input_dict, strict=True, from_attributes=True)
    assert settings.extra_body["dataSources"][0]["type"] == "AzureCosmosDB"


def test_azure_open_ai_chat_prompt_execution_settings_with_aisearch_data_sources():  # noqa: E501
    input_dict = {
        "messages": [{"role": "system", "content": "Hello"}],
        "extra_body": {
            "dataSources": [
                {
                    "type": "AzureCognitiveSearch",
                    "parameters": {
                        "authentication": {
                            "type": "APIKey",
                            "key": "****",
                        },
                        "endpoint": "https://****.search.windows.net/",
                        "indexName": "azuredocindex",
                        "queryType": "vector",
                        "embeddingDependency": {
                            "type": "DeploymentName",
                            "deploymentName": "{embedding deployment name}",
                        },
                        "fieldsMapping": {"vectorFields": ["contentvector"]},
                    },
                }
            ]
        },
    }
    settings = AzureChatPromptExecutionSettings.model_validate(input_dict, strict=True, from_attributes=True)
    assert settings.extra_body["dataSources"][0]["type"] == "AzureCognitiveSearch"
