from logging import Logger
import pytest

from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion_with_data import (
    AzureChatCompletionDataSourceConfig,
    AzureChatCompletionWithData,
)
from semantic_kernel.connectors.ai.chat_request_settings import ChatRequestSettings

from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import (
    AzureChatCompletion,
)


class TestAzureChatCompletionDataSourceConfig:
    def test_initialization_with_required_only(self):
        config = AzureChatCompletionDataSourceConfig(
            endpoint="test_endpoint", key="test_key", index_name="test_index"
        )

        # Required
        assert config._endpoint == "test_endpoint"
        assert config._key == "test_key"
        assert config._index_name == "test_index"
        # Optional, fallback to default
        assert config._type == "AzureCognitiveSearch"
        assert config._fields_mapping == None
        assert config._in_scope == True
        assert config._top_n_documents == 5
        assert config._query_type == "simple"
        assert config._semantic_configuration == None
        assert config._role_information == None
        assert config._filter == None
        assert config._embedding_endpoint == None
        assert config._embedding_key == None
        assert config._embedding_deployment_name == None

    def test_datasource_provide_both_embedding_configs(self):
        with pytest.raises(
            ValueError,
            match="Either provide embedding_endpoint and embedding_key or only embedding_deployment_name",
        ):
            config = AzureChatCompletionDataSourceConfig(
                endpoint="test_endpoint",
                key="test_key",
                index_name="test_index",
                embedding_endpoint="https://fake.embedding.endpoint.com",
                embedding_key="fakeEmbeddingKEY",
                embedding_deployment_name="fake-embedding-deployment-name",
            )

    def test_datasource_param(self):
        config = AzureChatCompletionDataSourceConfig(
            endpoint="test_endpoint",
            key="test_key",
            index_name="test_index",
            type="SomeNewType",
            fields_mapping={"field1": "mapped1", "field2": "mapped2"},
            in_scope=False,
            top_n_documents=42,
            query_type="semantic",
            semantic_configuration="default",
            role_information="You are a helpful bot",
            filter="someFilterPattern",
            embedding_endpoint="https://fake.embedding.endpoint.com",
            embedding_key="fakeEmbeddingKEY",
        )

        expected_output = {
            "type": "SomeNewType",
            "parameters": {
                "endpoint": "test_endpoint",
                "key": "test_key",
                "indexName": "test_index",
                "fieldsMapping": {"field1": "mapped1", "field2": "mapped2"},
                "inScope": False,
                "topNDocuments": 42,
                "queryType": "semantic",
                "semanticConfiguration": "default",
                "roleInformation": "You are a helpful bot",
                "filter": "someFilterPattern",
                "embeddingEndpoint": "https://fake.embedding.endpoint.com",
                "embeddingKey": "fakeEmbeddingKEY",
            },
        }

        assert config.as_datasource_param() == expected_output


class TestAzureChatCompletionWithData:
    @pytest.fixture
    def azure_chat_completion_with_data(self) -> AzureChatCompletionWithData:
        return AzureChatCompletionWithData(
            deployment_name="test_deployment",
            endpoint="https://test-endpoint.com",
            api_key="test_api_key",
            data_source_configs=[
                AzureChatCompletionDataSourceConfig(
                    endpoint="test_endpoint", key="test_key", index_name="test_index"
                )
            ],
        )

    def test_initialization(self):
        deployment_name = "test_deployment"
        endpoint = "https://test-endpoint.com"
        api_key = "test_api_key"
        api_version = "2023-08-01-preview"
        logger = Logger("test_logger")
        data_source_config = AzureChatCompletionDataSourceConfig(
            endpoint="test_endpoint", key="test_key", index_name="test_index"
        )

        # Test successful initialization
        azure_chat_completion_with_data = AzureChatCompletionWithData(
            deployment_name=deployment_name,
            endpoint=endpoint,
            api_key=api_key,
            api_version=api_version,
            logger=logger,
            data_source_configs=[data_source_config],
        )

        assert azure_chat_completion_with_data._endpoint == endpoint
        assert azure_chat_completion_with_data._api_version == api_version
        assert azure_chat_completion_with_data._api_type == "azure"
        assert azure_chat_completion_with_data._data_source_configs == [
            data_source_config
        ]
        assert isinstance(azure_chat_completion_with_data, AzureChatCompletion)

    def test_initialization_with_empty_data_source_configs(self):
        deployment_name = "test_deployment"
        endpoint = "https://test-endpoint.com"
        api_key = "test_api_key"

        with pytest.raises(ValueError, match="The data source configs cannot be empty"):
            AzureChatCompletionWithData(
                deployment_name=deployment_name,
                endpoint=endpoint,
                api_key=api_key,
                data_source_configs=[],
            )

    def test_initialize_with_unsupported_api_version(self):
        deployment_name = "test_deployment"
        endpoint = "https://test-endpoint.com"
        api_key = "test_api_key"
        data_source_config = AzureChatCompletionDataSourceConfig(
            endpoint="test_endpoint", key="test_key", index_name="test_index"
        )

        with pytest.raises(
            ValueError, match='Only API version "2023-08-01-preview" is supported'
        ):
            AzureChatCompletionWithData(
                deployment_name=deployment_name,
                endpoint=endpoint,
                api_key=api_key,
                data_source_configs=[data_source_config],
                api_version="2023-06-01-preview",
            )

    def test_functions_not_supported(self, azure_chat_completion_with_data):
        with pytest.raises(
            ValueError, match="Chat with your data API does not support function call"
        ):
            azure_chat_completion_with_data._validate_chat_request(
                messages=[{"role": "user", "text": "Hello"}],
                request_settings=ChatRequestSettings(function_call="auto"),
                stream=False,
                functions=[
                    {
                        "name": "get_current_weather",
                        "description": "Get the current weather in a given location",
                    }
                ],
            )

    def test_gen_payload(self, azure_chat_completion_with_data):
        payload = azure_chat_completion_with_data._gen_api_payload(
            messages=[{"role": "user", "text": "Hello"}],
            request_settings=ChatRequestSettings(function_call="auto"),
            stream=False,
        )

        expected = {
            "model": "test_deployment",
            "messages": [{"role": "user", "text": "Hello"}],
            "temperature": 0.0,
            "top_p": 1.0,
            "n": 1,
            "stream": False,
            "stop": None,
            "max_tokens": 256,
            "presence_penalty": 0.0,
            "frequency_penalty": 0.0,
            "logit_bias": {},
            "dataSources": [
                {
                    "type": "AzureCognitiveSearch",
                    "parameters": {
                        "endpoint": "test_endpoint",
                        "key": "test_key",
                        "indexName": "test_index",
                        "fieldsMapping": None,
                        "inScope": True,
                        "topNDocuments": 5,
                        "queryType": "simple",
                        "semanticConfiguration": None,
                        "roleInformation": None,
                        "filter": None,
                    },
                },
            ],
        }

        assert payload == expected

    def test_gen_headers_azure(self, azure_chat_completion_with_data):
        headers = azure_chat_completion_with_data._gen_api_headers()

        expected = {"Content-Type": "application/json", "Api-Key": "test_api_key"}

        assert headers == expected

    def test_gen_headers_azure_ad(self):
        conn = AzureChatCompletionWithData(
            deployment_name="test_deployment",
            endpoint="https://test-endpoint.com",
            api_key="test_api_key",
            data_source_configs=[
                AzureChatCompletionDataSourceConfig(
                    endpoint="test_endpoint", key="test_key", index_name="test_index"
                )
            ],
            ad_auth=True,
        )

        headers = conn._gen_api_headers()

        expected = {
            "Content-Type": "application/json",
            "Authorization": "Bearer test_api_key",
        }

        assert headers == expected

    def test_parse_2023_08_01_preview_response(self, azure_chat_completion_with_data):
        resp = {
            # Fields like id, model, created, and object are not parsed
            "choices": [
                {
                    "index": 0,
                    "finish_reason": "stop",
                    "message": {
                        "role": "assistant",
                        "content": "Here's the answer.",
                        "end_turn": True,
                        "context": {
                            "messages": [
                                {
                                    "role": "tool",
                                    "content": '{"citations": [{"content": "Citation 1"}, {"content": "Citation 2"}]}',
                                    "end_turn": False,
                                }
                            ]
                        },
                    },
                }
            ]
        }
        result = azure_chat_completion_with_data._parse_response(resp)
        assert result == (
            "Here's the answer.",
            '{"citations": [{"content": "Citation 1"}, {"content": "Citation 2"}]}',
        )

    def test_parse_2023_08_01_preview_response_multiple_choices(
        self, azure_chat_completion_with_data
    ):
        resp = {
            # Fields like id, model, created, and object are not parsed
            "choices": [
                {
                    "index": 0,
                    "finish_reason": "stop",
                    "message": {
                        "role": "assistant",
                        "content": "Here's the answer.",
                        "end_turn": True,
                        "context": {
                            "messages": [
                                {
                                    "role": "tool",
                                    "content": '{"citations": [{"content": "Citation 1"}, {"content": "Citation 2"}]}',
                                    "end_turn": False,
                                }
                            ]
                        },
                    },
                },
                {
                    "index": 1,
                    "finish_reason": "stop",
                    "message": {
                        "role": "assistant",
                        "content": "Here's another answer.",
                        "end_turn": True,
                        "context": {
                            "messages": [
                                {
                                    "role": "tool",
                                    "content": '{"citations": [{"content": "Citation 3"}, {"content": "Citation 4"}]}',
                                    "end_turn": False,
                                }
                            ]
                        },
                    },
                },
            ]
        }
        result = azure_chat_completion_with_data._parse_response(resp)
        assert result == [
            (
                "Here's the answer.",
                '{"citations": [{"content": "Citation 1"}, {"content": "Citation 2"}]}',
            ),
            (
                "Here's another answer.",
                '{"citations": [{"content": "Citation 3"}, {"content": "Citation 4"}]}',
            ),
        ]
