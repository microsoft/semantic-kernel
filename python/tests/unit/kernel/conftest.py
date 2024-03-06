from typing import Callable, List
from unittest.mock import Mock

import pytest

from semantic_kernel.contents.streaming_text_content import StreamingTextContent
from semantic_kernel.events.function_invoked_event_args import FunctionInvokedEventArgs
from semantic_kernel.events.function_invoking_event_args import FunctionInvokingEventArgs
from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.kernel import Kernel
from semantic_kernel.services.ai_service_client_base import AIServiceClientBase


@pytest.fixture(scope="function")
def kernel() -> Kernel:
    return Kernel()


@pytest.fixture(scope="session")
def service() -> AIServiceClientBase:
    return AIServiceClientBase(service_id="service", ai_model_id="ai_model_id")


@pytest.fixture(scope="function")
def kernel_with_service(kernel: Kernel, service: AIServiceClientBase) -> Kernel:
    kernel.add_service(service)
    return kernel


@pytest.fixture(scope="function")
def kernel_with_handlers(kernel: Kernel) -> Kernel:
    def invoking_handler(kernel: Kernel, e: FunctionInvokingEventArgs) -> FunctionInvokingEventArgs:
        pass

    def invoked_handler(kernel: Kernel, e: FunctionInvokedEventArgs) -> FunctionInvokedEventArgs:
        pass

    kernel.add_function_invoking_handler(invoking_handler)
    kernel.add_function_invoked_handler(invoked_handler)

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
def create_mock_function() -> Callable:
    async def stream_func(*args, **kwargs) -> List[StreamingTextContent]:
        yield [StreamingTextContent(choice_index=0, text="test", metadata={})]

    def create_mock_function(name: str, value: str = "test") -> KernelFunction:
        kernel_function_metadata = KernelFunctionMetadata(
            name=name,
            plugin_name="TestPlugin",
            description="test description",
            parameters=[],
            is_prompt=True,
            is_asynchronous=True,
        )
        mock_function = Mock(spec=KernelFunction)
        mock_function.metadata = kernel_function_metadata
        mock_function.name = kernel_function_metadata.name
        mock_function.plugin_name = kernel_function_metadata.plugin_name
        mock_function.description = kernel_function_metadata.description
        mock_function.invoke.return_value = FunctionResult(function=mock_function.metadata, value=value, metadata={})
        mock_function.invoke_stream = stream_func

        return mock_function

    return create_mock_function
