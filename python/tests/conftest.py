# Copyright (c) Microsoft. All rights reserved.

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Annotated
from unittest.mock import MagicMock
from uuid import uuid4

import numpy as np
import pandas as pd
from pydantic import BaseModel
from pytest import fixture

from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIEmbeddingPromptExecutionSettings,
)
from semantic_kernel.data.record_definition.vector_store_model_decorator import vectorstoremodel
from semantic_kernel.data.record_definition.vector_store_model_definition import VectorStoreRecordDefinition
from semantic_kernel.data.record_definition.vector_store_record_fields import (
    VectorStoreRecordDataField,
    VectorStoreRecordKeyField,
    VectorStoreRecordVectorField,
)

if TYPE_CHECKING:
    from semantic_kernel.contents.chat_history import ChatHistory
    from semantic_kernel.filters.functions.function_invocation_context import FunctionInvocationContext
    from semantic_kernel.functions.kernel_function import KernelFunction
    from semantic_kernel.kernel import Kernel
    from semantic_kernel.services.ai_service_client_base import AIServiceClientBase


@fixture(scope="function")
def kernel() -> "Kernel":
    from semantic_kernel.kernel import Kernel

    return Kernel()


@fixture(scope="session")
def service() -> "AIServiceClientBase":
    from semantic_kernel.services.ai_service_client_base import AIServiceClientBase

    return AIServiceClientBase(service_id="service", ai_model_id="ai_model_id")


@fixture(scope="session")
def default_service() -> "AIServiceClientBase":
    from semantic_kernel.services.ai_service_client_base import AIServiceClientBase

    return AIServiceClientBase(service_id="default", ai_model_id="ai_model_id")


@fixture(scope="function")
def kernel_with_service(kernel: "Kernel", service: "AIServiceClientBase") -> "Kernel":
    kernel.add_service(service)
    return kernel


@fixture(scope="function")
def kernel_with_default_service(kernel: "Kernel", default_service: "AIServiceClientBase") -> "Kernel":
    kernel.add_service(default_service)
    return kernel


@fixture(scope="session")
def not_decorated_native_function() -> Callable:
    def not_decorated_native_function(arg1: str) -> str:
        return "test"

    return not_decorated_native_function


@fixture(scope="session")
def decorated_native_function() -> Callable:
    from semantic_kernel.functions.kernel_function_decorator import kernel_function

    @kernel_function(name="getLightStatus")
    def decorated_native_function(arg1: str) -> str:
        return "test"

    return decorated_native_function


@fixture(scope="session")
def custom_plugin_class():
    from semantic_kernel.functions.kernel_function_decorator import kernel_function

    class CustomPlugin:
        @kernel_function(name="getLightStatus")
        def decorated_native_function(self) -> str:
            return "test"

    return CustomPlugin


@fixture(scope="session")
def experimental_plugin_class():
    from semantic_kernel.functions.kernel_function_decorator import kernel_function
    from semantic_kernel.utils.experimental_decorator import experimental_class

    @experimental_class
    class ExperimentalPlugin:
        @kernel_function(name="getLightStatus")
        def decorated_native_function(self) -> str:
            return "test"

    return ExperimentalPlugin


@fixture(scope="session")
def create_mock_function() -> Callable:
    from semantic_kernel.contents.streaming_text_content import StreamingTextContent
    from semantic_kernel.functions.function_result import FunctionResult
    from semantic_kernel.functions.kernel_function import KernelFunction
    from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata

    async def stream_func(*args, **kwargs):
        yield [StreamingTextContent(choice_index=0, text="test", metadata={})]

    def create_mock_function(name: str, value: str = "test") -> "KernelFunction":
        kernel_function_metadata = KernelFunctionMetadata(
            name=name,
            plugin_name="TestPlugin",
            description="test description",
            parameters=[],
            is_prompt=True,
            is_asynchronous=True,
        )

        class CustomKernelFunction(KernelFunction):
            call_count: int = 0

            async def _invoke_internal_stream(
                self,
                context: "FunctionInvocationContext",
            ) -> None:
                self.call_count += 1
                context.result = FunctionResult(
                    function=kernel_function_metadata,
                    value=stream_func(),
                )

            async def _invoke_internal(self, context: "FunctionInvocationContext"):
                self.call_count += 1
                context.result = FunctionResult(function=kernel_function_metadata, value=value, metadata={})

        return CustomKernelFunction(metadata=kernel_function_metadata)

    return create_mock_function


@fixture(scope="function")
def get_tool_call_mock():
    from semantic_kernel.contents.function_call_content import FunctionCallContent

    tool_call_mock = MagicMock(spec=FunctionCallContent)
    tool_call_mock.split_name_dict.return_value = {"arg_name": "arg_value"}
    tool_call_mock.to_kernel_arguments.return_value = {"arg_name": "arg_value"}
    tool_call_mock.name = "test-function"
    tool_call_mock.function_name = "function"
    tool_call_mock.plugin_name = "test"
    tool_call_mock.arguments = {"arg_name": "arg_value"}
    tool_call_mock.ai_model_id = None
    tool_call_mock.metadata = {}
    tool_call_mock.index = 0
    tool_call_mock.parse_arguments.return_value = {"arg_name": "arg_value"}
    tool_call_mock.id = "test_id"

    return tool_call_mock


@fixture(scope="function")
def chat_history() -> "ChatHistory":
    from semantic_kernel.contents.chat_history import ChatHistory

    return ChatHistory()


@fixture(scope="function")
def prompt() -> str:
    return "test prompt"


# @fixture(autouse=True)
# def enable_debug_mode():
#     """Set `autouse=True` to enable easy debugging for tests.

#     How to debug:
#     1. Ensure [snoop](https://github.com/alexmojaki/snoop) is installed
#         (`pip install snoop`).
#     2. If you're doing print based debugging, use `pr` instead of `print`.
#         That is, convert `print(some_var)` to `pr(some_var)`.
#     3. If you want a trace of a particular functions calls, just add `ss()` as the first
#         line of the function.

#     Note:
#     ----
#         It's completely fine to leave `autouse=True` in the fixture. It doesn't affect
#         the tests unless you use `pr` or `ss` in any test.

#     Note:
#     ----
#         When you use `ss` or `pr` in a test, pylance or mypy will complain. This is
#         because they don't know that we're adding these functions to the builtins. The
#         tests will run fine though.
#     """
#     import builtins

#     try:
#         import snoop
#     except ImportError:
#         warnings.warn(
#             "Install snoop to enable trace debugging. `pip install snoop`",
#             ImportWarning,
#         )
#         return

#     builtins.ss = snoop.snoop(depth=4).__enter__
#     builtins.pr = snoop.pp


@fixture
def exclude_list(request):
    """Fixture that returns a list of environment variables to exclude."""
    return request.param if hasattr(request, "param") else []


@fixture
def override_env_param_dict(request):
    """Fixture that returns a dict of environment variables to override."""
    return request.param if hasattr(request, "param") else {}


@fixture()
def azure_openai_unit_test_env(monkeypatch, exclude_list, override_env_param_dict):
    """Fixture to set environment variables for AzureOpenAISettings."""
    if exclude_list is None:
        exclude_list = []

    if override_env_param_dict is None:
        override_env_param_dict = {}

    env_vars = {
        "AZURE_OPENAI_CHAT_DEPLOYMENT_NAME": "test_chat_deployment",
        "AZURE_OPENAI_TEXT_DEPLOYMENT_NAME": "test_text_deployment",
        "AZURE_OPENAI_EMBEDDING_DEPLOYMENT_NAME": "test_embedding_deployment",
        "AZURE_OPENAI_TEXT_TO_IMAGE_DEPLOYMENT_NAME": "test_text_to_image_deployment",
        "AZURE_OPENAI_AUDIO_TO_TEXT_DEPLOYMENT_NAME": "test_audio_to_text_deployment",
        "AZURE_OPENAI_TEXT_TO_AUDIO_DEPLOYMENT_NAME": "test_text_to_audio_deployment",
        "AZURE_OPENAI_API_KEY": "test_api_key",
        "AZURE_OPENAI_ENDPOINT": "https://test-endpoint.com",
        "AZURE_OPENAI_API_VERSION": "2023-03-15-preview",
        "AZURE_OPENAI_BASE_URL": "https://test_text_deployment.test-base-url.com",
        "AZURE_OPENAI_TOKEN_ENDPOINT": "https://test-token-endpoint.com",
    }

    env_vars.update(override_env_param_dict)

    for key, value in env_vars.items():
        if key not in exclude_list:
            monkeypatch.setenv(key, value)
        else:
            monkeypatch.delenv(key, raising=False)

    return env_vars


@fixture()
def openai_unit_test_env(monkeypatch, exclude_list, override_env_param_dict):
    """Fixture to set environment variables for OpenAISettings."""
    if exclude_list is None:
        exclude_list = []

    if override_env_param_dict is None:
        override_env_param_dict = {}

    env_vars = {
        "OPENAI_API_KEY": "test_api_key",
        "OPENAI_ORG_ID": "test_org_id",
        "OPENAI_CHAT_MODEL_ID": "test_chat_model_id",
        "OPENAI_TEXT_MODEL_ID": "test_text_model_id",
        "OPENAI_EMBEDDING_MODEL_ID": "test_embedding_model_id",
        "OPENAI_TEXT_TO_IMAGE_MODEL_ID": "test_text_to_image_model_id",
        "OPENAI_AUDIO_TO_TEXT_MODEL_ID": "test_audio_to_text_model_id",
        "OPENAI_TEXT_TO_AUDIO_MODEL_ID": "test_text_to_audio_model_id",
    }

    env_vars.update(override_env_param_dict)

    for key, value in env_vars.items():
        if key not in exclude_list:
            monkeypatch.setenv(key, value)
        else:
            monkeypatch.delenv(key, raising=False)

    return env_vars


@fixture()
def mistralai_unit_test_env(monkeypatch, exclude_list, override_env_param_dict):
    """Fixture to set environment variables for MistralAISettings."""
    if exclude_list is None:
        exclude_list = []

    if override_env_param_dict is None:
        override_env_param_dict = {}

    env_vars = {
        "MISTRALAI_CHAT_MODEL_ID": "test_chat_model_id",
        "MISTRALAI_API_KEY": "test_api_key",
        "MISTRALAI_EMBEDDING_MODEL_ID": "test_embedding_model_id",
    }

    env_vars.update(override_env_param_dict)

    for key, value in env_vars.items():
        if key not in exclude_list:
            monkeypatch.setenv(key, value)
        else:
            monkeypatch.delenv(key, raising=False)

    return env_vars


@fixture()
def anthropic_unit_test_env(monkeypatch, exclude_list, override_env_param_dict):
    """Fixture to set environment variables for AnthropicSettings."""
    if exclude_list is None:
        exclude_list = []

    if override_env_param_dict is None:
        override_env_param_dict = {}

    env_vars = {"ANTHROPIC_CHAT_MODEL_ID": "test_chat_model_id", "ANTHROPIC_API_KEY": "test_api_key"}

    env_vars.update(override_env_param_dict)

    for key, value in env_vars.items():
        if key not in exclude_list:
            monkeypatch.setenv(key, value)
        else:
            monkeypatch.delenv(key, raising=False)

    return env_vars


@fixture()
def aca_python_sessions_unit_test_env(monkeypatch, exclude_list, override_env_param_dict):
    """Fixture to set environment variables for ACA Python Unit Tests."""
    if exclude_list is None:
        exclude_list = []

    if override_env_param_dict is None:
        override_env_param_dict = {}

    env_vars = {
        "ACA_POOL_MANAGEMENT_ENDPOINT": "https://test.endpoint/",
    }

    env_vars.update(override_env_param_dict)

    for key, value in env_vars.items():
        if key not in exclude_list:
            monkeypatch.setenv(key, value)
        else:
            monkeypatch.delenv(key, raising=False)

    return env_vars


@fixture()
def azure_ai_search_unit_test_env(monkeypatch, exclude_list, override_env_param_dict):
    """Fixture to set environment variables for ACA Python Unit Tests."""
    if exclude_list is None:
        exclude_list = []

    if override_env_param_dict is None:
        override_env_param_dict = {}

    env_vars = {
        "AZURE_AI_SEARCH_API_KEY": "test-api-key",
        "AZURE_AI_SEARCH_ENDPOINT": "https://test-endpoint.com",
        "AZURE_AI_SEARCH_INDEX_NAME": "test-index-name",
    }

    env_vars.update(override_env_param_dict)

    for key, value in env_vars.items():
        if key not in exclude_list:
            monkeypatch.setenv(key, value)
        else:
            monkeypatch.delenv(key, raising=False)

    return env_vars


@fixture()
def bing_unit_test_env(monkeypatch, exclude_list, override_env_param_dict):
    """Fixture to set environment variables for BingConnector."""
    if exclude_list is None:
        exclude_list = []

    if override_env_param_dict is None:
        override_env_param_dict = {}

    env_vars = {
        "BING_API_KEY": "test_api_key",
        "BING_CUSTOM_CONFIG": "test_org_id",
    }

    env_vars.update(override_env_param_dict)

    for key, value in env_vars.items():
        if key not in exclude_list:
            monkeypatch.setenv(key, value)
        else:
            monkeypatch.delenv(key, raising=False)

    return env_vars


@fixture()
def google_search_unit_test_env(monkeypatch, exclude_list, override_env_param_dict):
    """Fixture to set environment variables for the Google Search Connector."""
    if exclude_list is None:
        exclude_list = []

    if override_env_param_dict is None:
        override_env_param_dict = {}

    env_vars = {
        "GOOGLE_SEARCH_API_KEY": "test_api_key",
        "GOOGLE_SEARCH_ENGINE_ID": "test_id",
    }

    env_vars.update(override_env_param_dict)

    for key, value in env_vars.items():
        if key not in exclude_list:
            monkeypatch.setenv(key, value)
        else:
            monkeypatch.delenv(key, raising=False)

    return env_vars


@fixture
def postgres_unit_test_env(monkeypatch, exclude_list, override_env_param_dict):
    """Fixture to set environment variables for Postgres connector."""
    if exclude_list is None:
        exclude_list = []

    if override_env_param_dict is None:
        override_env_param_dict = {}

    env_vars = {"POSTGRES_CONNECTION_STRING": "host=localhost port=5432 dbname=postgres user=testuser password=example"}

    env_vars.update(override_env_param_dict)

    for key, value in env_vars.items():
        if key not in exclude_list:
            monkeypatch.setenv(key, value)
        else:
            monkeypatch.delenv(key, raising=False)

    return env_vars


@fixture
def qdrant_unit_test_env(monkeypatch, exclude_list, override_env_param_dict):
    """Fixture to set environment variables for QdrantConnector."""
    if exclude_list is None:
        exclude_list = []

    if override_env_param_dict is None:
        override_env_param_dict = {}

    env_vars = {"QDRANT_LOCATION": "http://localhost:6333"}

    env_vars.update(override_env_param_dict)

    for key, value in env_vars.items():
        if key not in exclude_list:
            monkeypatch.setenv(key, value)
        else:
            monkeypatch.delenv(key, raising=False)

    return env_vars


@fixture
def redis_unit_test_env(monkeypatch, exclude_list, override_env_param_dict):
    """Fixture to set environment variables for Redis."""
    if exclude_list is None:
        exclude_list = []

    if override_env_param_dict is None:
        override_env_param_dict = {}

    env_vars = {"REDIS_CONNECTION_STRING": "redis://localhost:6379"}

    env_vars.update(override_env_param_dict)

    for key, value in env_vars.items():
        if key not in exclude_list:
            monkeypatch.setenv(key, value)
        else:
            monkeypatch.delenv(key, raising=False)

    return env_vars


@fixture
def index_kind(request) -> str:
    if hasattr(request, "param"):
        return request.param
    return "hnsw"


@fixture
def distance_function(request) -> str:
    if hasattr(request, "param"):
        return request.param
    return "cosine_similarity"


@fixture
def vector_property_type(request) -> str:
    if hasattr(request, "param"):
        return request.param
    return "float"


@fixture
def dimensions(request) -> int:
    if hasattr(request, "param"):
        return request.param
    return 5


@fixture
def dataclass_vector_data_model(
    index_kind: str, distance_function: str, vector_property_type: str, dimensions: int
) -> object:
    @vectorstoremodel
    @dataclass
    class MyDataModel:
        vector: Annotated[
            list[float] | None,
            VectorStoreRecordVectorField(
                embedding_settings={"default": OpenAIEmbeddingPromptExecutionSettings(dimensions=1536)},
                index_kind=index_kind,
                dimensions=dimensions,
                distance_function=distance_function,
                property_type=vector_property_type,
            ),
        ] = None
        id: Annotated[str, VectorStoreRecordKeyField()] = field(default_factory=lambda: str(uuid4()))
        content: Annotated[
            str, VectorStoreRecordDataField(has_embedding=True, embedding_property_name="vector", property_type="str")
        ] = "content1"

    return MyDataModel


@fixture
def dataclass_vector_data_model_array(
    index_kind: str, distance_function: str, vector_property_type: str, dimensions: int
) -> object:
    @vectorstoremodel
    @dataclass
    class MyDataModel:
        vector: Annotated[
            list[float] | None,
            VectorStoreRecordVectorField(
                embedding_settings={"default": OpenAIEmbeddingPromptExecutionSettings(dimensions=1536)},
                index_kind=index_kind,
                dimensions=dimensions,
                distance_function=distance_function,
                property_type=vector_property_type,
                serialize_function=np.ndarray.tolist,
                deserialize_function=np.array,
            ),
        ] = None
        id: Annotated[str, VectorStoreRecordKeyField()] = field(default_factory=lambda: str(uuid4()))
        content: Annotated[
            str, VectorStoreRecordDataField(has_embedding=True, embedding_property_name="vector", property_type="str")
        ] = "content1"

    return MyDataModel


@fixture
def data_model_definition(
    index_kind: str, distance_function: str, vector_property_type: str, dimensions: int
) -> object:
    return VectorStoreRecordDefinition(
        fields={
            "id": VectorStoreRecordKeyField(),
            "content": VectorStoreRecordDataField(
                has_embedding=True,
                embedding_property_name="vector",
            ),
            "vector": VectorStoreRecordVectorField(
                dimensions=dimensions,
                index_kind=index_kind,
                distance_function=distance_function,
                property_type=vector_property_type,
            ),
        }
    )


@fixture
def data_model_definition_pandas(
    index_kind: str, distance_function: str, vector_property_type: str, dimensions: int
) -> object:
    return VectorStoreRecordDefinition(
        fields={
            "vector": VectorStoreRecordVectorField(
                name="vector",
                index_kind=index_kind,
                dimensions=dimensions,
                distance_function=distance_function,
                property_type=vector_property_type,
            ),
            "id": VectorStoreRecordKeyField(name="id"),
            "content": VectorStoreRecordDataField(
                name="content", has_embedding=True, embedding_property_name="vector", property_type="str"
            ),
        },
        container_mode=True,
        to_dict=lambda x: x.to_dict(orient="records"),
        from_dict=lambda x, **_: pd.DataFrame(x),
    )


@fixture
def data_model_type(index_kind: str, distance_function: str, vector_property_type: str, dimensions: int) -> object:
    @vectorstoremodel
    class DataModelClass(BaseModel):
        content: Annotated[str, VectorStoreRecordDataField(has_embedding=True, embedding_property_name="vector")]
        vector: Annotated[
            list[float],
            VectorStoreRecordVectorField(
                index_kind=index_kind,
                distance_function=distance_function,
                property_type=vector_property_type,
                dimensions=dimensions,
            ),
        ]
        id: Annotated[str, VectorStoreRecordKeyField()]

    return DataModelClass


@fixture
def data_model_type_with_key_as_key_field(
    index_kind: str, distance_function: str, vector_property_type: str, dimensions: int
) -> object:
    """Data model type with key as key field."""

    @vectorstoremodel
    class DataModelClass(BaseModel):
        content: Annotated[str, VectorStoreRecordDataField(has_embedding=True, embedding_property_name="vector")]
        vector: Annotated[
            list[float],
            VectorStoreRecordVectorField(
                index_kind=index_kind,
                distance_function=distance_function,
                property_type=vector_property_type,
                dimensions=dimensions,
            ),
        ]
        key: Annotated[str, VectorStoreRecordKeyField()]

    return DataModelClass
