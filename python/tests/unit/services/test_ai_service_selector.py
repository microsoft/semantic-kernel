# Copyright (c) Microsoft. All rights reserved.


from pytest import raises

from semantic_kernel.connectors.ai.prompt_execution_settings import (
    PromptExecutionSettings,
)
from semantic_kernel.exceptions.kernel_exceptions import KernelServiceNotFoundError
from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.kernel import Kernel
from semantic_kernel.services.ai_service_client_base import AIServiceClientBase
from semantic_kernel.services.ai_service_selector import AIServiceSelector


class CustomFunction(KernelFunction):
    prompt_execution_settings: dict[str, PromptExecutionSettings] = {}

    async def _invoke_internal(self, context) -> None:
        context.result = FunctionResult(
            function=self.metadata, value="internal invoke passed"
        )

    async def _invoke_internal_stream(self, context) -> None:
        context.result = FunctionResult(
            function=self.metadata, value="internal invoke stream passed"
        )


def test_ai_service_selector():
    service_selector = AIServiceSelector()
    assert service_selector is not None


def test_select_ai_service_no_default(kernel_with_service: Kernel):
    function = CustomFunction(
        metadata=KernelFunctionMetadata(
            name="test", plugin_name="test", description="test", is_prompt=True
        ),
        prompt_execution_settings={},
    )
    kernel_with_service.add_function(plugin_name="test", function=function)
    service_selector = kernel_with_service.ai_service_selector
    service, settings = service_selector.select_ai_service(
        kernel_with_service, function, KernelArguments(), type_=AIServiceClientBase
    )
    assert service is not None
    assert service.service_id != "default"
    assert settings is not None


def test_select_ai_service_no_default_default_types(kernel_with_service: Kernel):
    function = CustomFunction(
        metadata=KernelFunctionMetadata(
            name="test", plugin_name="test", description="test", is_prompt=True
        ),
        prompt_execution_settings={},
    )
    kernel_with_service.add_function(plugin_name="test", function=function)
    service_selector = kernel_with_service.ai_service_selector
    with raises(KernelServiceNotFoundError):
        service_selector.select_ai_service(
            kernel_with_service, function, KernelArguments()
        )


def test_select_ai_service_default_no_type(kernel_with_default_service: Kernel):
    function = CustomFunction(
        metadata=KernelFunctionMetadata(
            name="test", plugin_name="test", description="test", is_prompt=True
        ),
        prompt_execution_settings={},
    )
    kernel_with_default_service.add_function(plugin_name="test", function=function)
    service_selector = kernel_with_default_service.ai_service_selector
    with raises(KernelServiceNotFoundError):
        service_selector.select_ai_service(
            kernel_with_default_service, function, KernelArguments()
        )


def test_select_ai_service_default(kernel_with_default_service: Kernel):
    function = CustomFunction(
        metadata=KernelFunctionMetadata(
            name="test", plugin_name="test", description="test", is_prompt=True
        ),
        prompt_execution_settings={},
    )
    kernel_with_default_service.add_function(plugin_name="test", function=function)
    service_selector = kernel_with_default_service.ai_service_selector
    service, settings = service_selector.select_ai_service(
        kernel_with_default_service,
        function,
        KernelArguments(),
        type_=AIServiceClientBase,
    )
    assert service is not None
    assert settings is not None


def test_select_ai_service_settings_through_arguments(kernel_with_service: Kernel):
    function = CustomFunction(
        metadata=KernelFunctionMetadata(
            name="test", plugin_name="test", description="test", is_prompt=True
        ),
        prompt_execution_settings={},
    )
    kernel_with_service.add_function(plugin_name="test", function=function)
    service_selector = kernel_with_service.ai_service_selector
    service, settings = service_selector.select_ai_service(
        kernel_with_service,
        function,
        KernelArguments(settings={"service": PromptExecutionSettings()}),
        type_=AIServiceClientBase,
    )
    assert service is not None
    assert settings is not None


def test_select_ai_service_settings_through_function(kernel_with_service: Kernel):
    function = CustomFunction(
        metadata=KernelFunctionMetadata(
            name="test", plugin_name="test", description="test", is_prompt=True
        ),
        prompt_execution_settings={"service": PromptExecutionSettings()},
    )
    kernel_with_service.add_function(plugin_name="test", function=function)
    service_selector = kernel_with_service.ai_service_selector
    service, settings = service_selector.select_ai_service(
        kernel_with_service, function, KernelArguments(), type_=AIServiceClientBase
    )
    assert service is not None
    assert settings is not None
