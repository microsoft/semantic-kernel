# Copyright (c) Microsoft. All rights reserved.

import warnings
from typing import Callable

import pytest

from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.filters.functions.function_invocation_context import FunctionInvocationContext
from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.kernel import Kernel
from semantic_kernel.services.ai_service_client_base import AIServiceClientBase


@pytest.fixture(scope="function")
def kernel() -> "Kernel":
    from semantic_kernel.kernel import Kernel

    return Kernel()


@pytest.fixture(scope="session")
def service() -> "AIServiceClientBase":
    from semantic_kernel.services.ai_service_client_base import AIServiceClientBase

    return AIServiceClientBase(service_id="service", ai_model_id="ai_model_id")


@pytest.fixture(scope="session")
def default_service() -> "AIServiceClientBase":
    from semantic_kernel.services.ai_service_client_base import AIServiceClientBase

    return AIServiceClientBase(service_id="default", ai_model_id="ai_model_id")


@pytest.fixture(scope="function")
def kernel_with_service(kernel: "Kernel", service: "AIServiceClientBase") -> "Kernel":
    kernel.add_service(service)
    return kernel


@pytest.fixture(scope="function")
def kernel_with_default_service(kernel: "Kernel", default_service: "AIServiceClientBase") -> "Kernel":
    kernel.add_service(default_service)
    return kernel


@pytest.fixture(scope="session")
def not_decorated_native_function() -> Callable:
    def not_decorated_native_function(arg1: str) -> str:
        return "test"

    return not_decorated_native_function


@pytest.fixture(scope="session")
def decorated_native_function() -> Callable:
    @kernel_function(name="getLightStatus")
    def decorated_native_function(arg1: str) -> str:
        return "test"

    return decorated_native_function


@pytest.fixture(scope="session")
def custom_plugin_class():
    class CustomPlugin:
        @kernel_function(name="getLightStatus")
        def decorated_native_function(self) -> str:
            return "test"

    return CustomPlugin


@pytest.fixture(scope="session")
def experimental_plugin_class():
    from semantic_kernel.functions.kernel_function_decorator import kernel_function
    from semantic_kernel.utils.experimental_decorator import experimental_class

    @experimental_class
    class ExperimentalPlugin:
        @kernel_function(name="getLightStatus")
        def decorated_native_function(self) -> str:
            return "test"

    return ExperimentalPlugin


@pytest.fixture(scope="session")
def create_mock_function() -> Callable:
    from semantic_kernel.functions.kernel_function import KernelFunction

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

        mock_function = CustomKernelFunction(metadata=kernel_function_metadata)

        return mock_function

    return create_mock_function


@pytest.fixture(scope="function")
def chat_history():
    return ChatHistory()


@pytest.fixture(autouse=True)
def enable_debug_mode():
    """Set `autouse=True` to enable easy debugging for tests.

    How to debug:
    1. Ensure [snoop](https://github.com/alexmojaki/snoop) is installed
        (`pip install snoop`).
    2. If you're doing print based debugging, use `pr` instead of `print`.
        That is, convert `print(some_var)` to `pr(some_var)`.
    3. If you want a trace of a particular functions calls, just add `ss()` as the first
        line of the function.

    NOTE:
    ----
        It's completely fine to leave `autouse=True` in the fixture. It doesn't affect
        the tests unless you use `pr` or `ss` in any test.

    NOTE:
    ----
        When you use `ss` or `pr` in a test, pylance or mypy will complain. This is
        because they don't know that we're adding these functions to the builtins. The
        tests will run fine though.
    """
    import builtins

    try:
        import snoop
    except ImportError:
        warnings.warn(
            "Install snoop to enable trace debugging. `pip install snoop`",
            ImportWarning,
        )
        return

    builtins.ss = snoop.snoop(depth=4).__enter__
    builtins.pr = snoop.pp


@pytest.fixture
def exclude_list(request):
    """Fixture that returns a list of environment variables to exclude."""
    return request.param if hasattr(request, "param") else []


@pytest.fixture
def override_env_param_dict(request):
    """Fixture that returns a dict of environment variables to override."""
    return request.param if hasattr(request, "param") else {}


@pytest.fixture()
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
        "AZURE_OPENAI_API_KEY": "test_api_key",
        "AZURE_OPENAI_ENDPOINT": "https://test-endpoint.com",
        "AZURE_OPENAI_API_VERSION": "2023-03-15-preview",
        "AZURE_OPENAI_BASE_URL": "https://test_text_deployment.test-base-url.com",
    }

    env_vars.update(override_env_param_dict)

    for key, value in env_vars.items():
        if key not in exclude_list:
            monkeypatch.setenv(key, value)
        else:
            monkeypatch.delenv(key, raising=False)

    return env_vars


@pytest.fixture()
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
    }

    env_vars.update(override_env_param_dict)

    for key, value in env_vars.items():
        if key not in exclude_list:
            monkeypatch.setenv(key, value)
        else:
            monkeypatch.delenv(key, raising=False)

    return env_vars


@pytest.fixture()
def google_palm_unit_test_env(monkeypatch, exclude_list, override_env_param_dict):
    """Fixture to set environment variables for Google Palm."""
    if exclude_list is None:
        exclude_list = []

    if override_env_param_dict is None:
        override_env_param_dict = {}

    env_vars = {
        "GOOGLE_PALM_API_KEY": "test_api_key",
        "OPENAI_CHAT_MODEL_ID": "test_chat_model_id",
        "OPENAI_TEXT_MODEL_ID": "test_text_model_id",
        "OPENAI_EMBEDDING_MODEL_ID": "test_embedding_model_id",
    }

    env_vars.update(override_env_param_dict)

    for key, value in env_vars.items():
        if key not in exclude_list:
            monkeypatch.setenv(key, value)
        else:
            monkeypatch.delenv(key, raising=False)

    return env_vars


@pytest.fixture()
def aca_python_sessions_unit_test_env(monkeypatch, exclude_list, override_env_param_dict):
    """Fixture to set environment variables for ACA Python Unit Tests."""
    if exclude_list is None:
        exclude_list = []

    if override_env_param_dict is None:
        override_env_param_dict = {}

    env_vars = {
        "ACA_POOL_MANAGEMENT_ENDPOINT": "https://test.endpoint/python/excute/",
    }

    env_vars.update(override_env_param_dict)

    for key, value in env_vars.items():
        if key not in exclude_list:
            monkeypatch.setenv(key, value)
        else:
            monkeypatch.delenv(key, raising=False)

    return env_vars


@pytest.fixture()
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
