# Copyright (c) Microsoft. All rights reserved.

import os
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Union
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion import OpenAIChatCompletion
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.const import METADATA_EXCEPTION_KEY
from semantic_kernel.contents import ChatMessageContent
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.exceptions import KernelFunctionAlreadyExistsError, KernelServiceNotFoundError
from semantic_kernel.exceptions.content_exceptions import FunctionCallInvalidArgumentsException
from semantic_kernel.exceptions.kernel_exceptions import (
    KernelFunctionNotFoundError,
    KernelInvokeException,
    KernelPluginNotFoundError,
    OperationCancelledException,
)
from semantic_kernel.exceptions.template_engine_exceptions import TemplateSyntaxError
from semantic_kernel.filters.filter_types import FilterTypes
from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata
from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.prompt_template.kernel_prompt_template import KernelPromptTemplate
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig
from semantic_kernel.services.ai_service_client_base import AIServiceClientBase
from semantic_kernel.services.ai_service_selector import AIServiceSelector


# region Init
def test_init():
    kernel = Kernel()
    assert kernel is not None
    assert kernel.ai_service_selector is not None
    assert kernel.plugins is not None
    assert kernel.services is not None
    assert kernel.retry_mechanism is not None
    assert kernel.function_invocation_filters is not None
    assert kernel.prompt_rendering_filters is not None


def test_kernel_init_with_ai_service_selector():
    ai_service_selector = AIServiceSelector()
    kernel = Kernel(ai_service_selector=ai_service_selector)
    assert kernel.ai_service_selector is not None


def test_kernel_init_with_services(service: AIServiceClientBase):
    kernel = Kernel(services=service)
    assert kernel.services is not None
    assert kernel.services["service"] is not None


def test_kernel_init_with_services_dict(service: AIServiceClientBase):
    kernel = Kernel(services={"service": service})
    assert kernel.services is not None
    assert kernel.services["service"] is not None


def test_kernel_init_with_services_list(service: AIServiceClientBase):
    kernel = Kernel(services=[service])
    assert kernel.services is not None
    assert kernel.services["service"] is not None


def test_kernel_init_with_plugins():
    plugins = {"plugin": KernelPlugin(name="plugin")}
    kernel = Kernel(plugins=plugins)
    assert kernel.plugins is not None


def test_kernel_init_with_kernel_plugin_instance():
    plugin = KernelPlugin(name="plugin")
    kernel = Kernel(plugins=plugin)
    assert kernel.plugins is not None


def test_kernel_init_with_kernel_plugin_list():
    plugin = [KernelPlugin(name="plugin")]
    kernel = Kernel(plugins=plugin)
    assert kernel.plugins is not None


# endregion
# region Invoke Functions


async def test_invoke_function(kernel: Kernel, create_mock_function):
    mock_function = create_mock_function(name="test_function")

    await kernel.invoke(mock_function, KernelArguments())

    assert mock_function.call_count == 1


async def test_invoke_function_with_cancellation(kernel: Kernel, create_mock_function):
    mock_function = create_mock_function(name="test_function")

    with (
        patch.object(Kernel, "invoke", AsyncMock(side_effect=OperationCancelledException("Operation cancelled"))),
        pytest.raises(OperationCancelledException),
    ):
        result = await kernel.invoke(function=mock_function, arguments=KernelArguments())

        assert result is None

        Kernel.invoke.assert_called_once_with(function=mock_function, arguments=KernelArguments())


async def test_invoke_functions_by_name(kernel: Kernel, create_mock_function):
    mock_function = kernel.add_function(plugin_name="test", function=create_mock_function(name="test_function"))

    result = await kernel.invoke(function_name="test_function", plugin_name="test", arguments=KernelArguments())
    assert str(result) == "test"

    assert mock_function.call_count == 1

    async for response in kernel.invoke_stream(function_name="test_function", plugin_name="test"):
        assert response[0].text == "test"


async def test_invoke_functions_by_name_return_function_results(kernel: Kernel, create_mock_function):
    mock_function = kernel.add_function(plugin_name="test", function=create_mock_function(name="test_function"))

    result = await kernel.invoke(function_name="test_function", plugin_name="test", arguments=KernelArguments())
    assert str(result) == "test"

    assert mock_function.call_count == 1

    async for _ in kernel.invoke_stream(
        function_name="test_function", plugin_name="test", return_function_results=True
    ):
        assert isinstance(result, FunctionResult)


async def test_invoke_function_fail(kernel: Kernel, create_mock_function):
    mock_function = create_mock_function(name="test_function")
    kernel.add_plugin(KernelPlugin(name="test", functions=[mock_function]))

    with pytest.raises(KernelFunctionNotFoundError):
        await kernel.invoke(arguments=KernelArguments())

    with pytest.raises(KernelFunctionNotFoundError):
        async for _ in kernel.invoke_stream(arguments=KernelArguments()):
            pass


async def test_invoke_function_cancelled(kernel: Kernel, create_mock_function):
    mock_function = create_mock_function(name="test_function")
    mock_function._invoke_internal = AsyncMock(side_effect=OperationCancelledException("Operation cancelled"))
    kernel.add_plugin(KernelPlugin(name="test", functions=[mock_function]))

    result = await kernel.invoke(mock_function, arguments=KernelArguments())
    assert result is None


async def test_invoke_stream_function(kernel: Kernel, create_mock_function):
    mock_function = create_mock_function(name="test_function")
    mock_function = kernel.add_function(plugin_name="test", function=mock_function)

    async for part in kernel.invoke_stream(mock_function, input="test"):
        assert part[0].text == "test"

    assert mock_function.call_count == 1


async def test_invoke_stream_functions_throws_exception(kernel: Kernel, create_mock_function):
    mock_function = create_mock_function(name="test_function")
    kernel.add_plugin(KernelPlugin(name="test", functions=[mock_function]))
    functions = [mock_function]

    function_result_with_exception = FunctionResult(
        value="", function=mock_function.metadata, output=None, metadata={METADATA_EXCEPTION_KEY: "Test Exception"}
    )

    with patch("semantic_kernel.kernel.Kernel.invoke_stream", return_value=AsyncMock()) as mocked_invoke_stream:
        mocked_invoke_stream.return_value.__aiter__.return_value = [function_result_with_exception]

        async for part in kernel.invoke_stream(functions, input="test"):
            assert METADATA_EXCEPTION_KEY in part.metadata, "Expected exception metadata in the FunctionResult."
            assert part.metadata[METADATA_EXCEPTION_KEY] == "Test Exception", "The exception message does not match."
            break


async def test_invoke_prompt(kernel: Kernel, create_mock_function):
    mock_function = create_mock_function(name="test_function")
    with patch(
        "semantic_kernel.functions.kernel_function_from_prompt.KernelFunctionFromPrompt._invoke_internal",
        return_value=FunctionResult(function=mock_function.metadata, value="test"),
    ) as mock_invoke:
        await kernel.invoke_prompt(prompt="test", plugin_name="test", function_name="test", arguments=KernelArguments())
        mock_invoke.invoke.call_count == 1


async def test_invoke_prompt_no_prompt_error(kernel: Kernel):
    with pytest.raises(TemplateSyntaxError):
        await kernel.invoke_prompt(
            function_name="test_function",
            plugin_name="test_plugin",
            prompt="",
        )


async def test_invoke_prompt_stream_no_prompt_throws(kernel: Kernel):
    with pytest.raises(TemplateSyntaxError):
        async for _ in kernel.invoke_prompt_stream(prompt=""):
            pass


async def test_invoke_prompt_stream(kernel: Kernel, create_mock_function):
    mock_function = create_mock_function(name="test_function")
    with (
        patch(
            "semantic_kernel.kernel.Kernel.invoke_stream",
        ) as mock_stream_invoke,
    ):
        mock_stream_invoke.return_value.__aiter__.return_value = [
            FunctionResult(function=mock_function.metadata, value="test")
        ]
        async for response in kernel.invoke_prompt_stream(prompt="test"):
            assert response.value == "test"


async def test_invoke_prompt_stream_returns_function_results(kernel: Kernel, create_mock_function):
    mock_function = create_mock_function(name="test_function")
    with (
        patch(
            "semantic_kernel.kernel.Kernel.invoke_stream",
        ) as mock_stream_invoke,
    ):
        mock_stream_invoke.return_value.__aiter__.return_value = [
            FunctionResult(function=mock_function.metadata, value="test")
        ]
        async for response in kernel.invoke_prompt_stream(prompt="test", return_function_results=True):
            assert isinstance(response, FunctionResult)


async def test_invoke_prompt_stream_raises_exception(kernel: Kernel, create_mock_function):
    mock_function = create_mock_function(name="test_function")
    with (
        patch(
            "semantic_kernel.kernel.Kernel.invoke_stream",
        ) as mock_stream_invoke,
        pytest.raises(KernelInvokeException),
    ):
        mock_stream_invoke.return_value.__aiter__.return_value = [
            FunctionResult(
                function=mock_function.metadata, value="", metadata={METADATA_EXCEPTION_KEY: KernelInvokeException()}
            )
        ]
        async for _ in kernel.invoke_prompt_stream(prompt="test"):
            pass


async def test_invoke_function_call(kernel: Kernel, get_tool_call_mock):
    tool_call_mock = get_tool_call_mock
    result_mock = MagicMock(spec=ChatMessageContent)
    result_mock.items = [tool_call_mock]
    chat_history_mock = MagicMock(spec=ChatHistory)

    func_mock = AsyncMock(spec=KernelFunction)
    func_meta = KernelFunctionMetadata(name="function", is_prompt=False)
    func_mock.metadata = func_meta
    func_mock.name = "function"
    func_result = FunctionResult(value="Function result", function=func_meta)
    func_mock.invoke = MagicMock(return_value=func_result)

    arguments = KernelArguments()

    with (
        patch("semantic_kernel.kernel.logger", autospec=True),
        patch("semantic_kernel.kernel.Kernel.get_list_of_function_metadata", return_value=[func_meta]),
    ):
        await kernel.invoke_function_call(
            function_call=tool_call_mock,
            chat_history=chat_history_mock,
            arguments=arguments,
            function_call_count=1,
            request_index=0,
            function_behavior=FunctionChoiceBehavior.Auto(filters={"included_functions": ["function"]}),
        )


async def test_invoke_function_call_throws_during_invoke(kernel: Kernel, get_tool_call_mock):
    tool_call_mock = get_tool_call_mock
    result_mock = MagicMock(spec=ChatMessageContent)
    result_mock.items = [tool_call_mock]
    chat_history_mock = MagicMock(spec=ChatHistory)
    chat_history_mock.messages = [MagicMock(spec=StreamingChatMessageContent)]

    func_mock = AsyncMock(spec=KernelFunction)
    func_meta = KernelFunctionMetadata(name="function", is_prompt=False)
    func_mock.metadata = func_meta
    func_mock.name = "function"
    func_result = FunctionResult(value="Function result", function=func_meta)
    func_mock.invoke = MagicMock(return_value=func_result)

    arguments = KernelArguments()

    with (
        patch("semantic_kernel.kernel.logger", autospec=True),
        patch("semantic_kernel.kernel.Kernel.get_list_of_function_metadata", return_value=[func_meta]),
        patch("semantic_kernel.kernel.Kernel.get_function", return_value=func_mock),
    ):
        await kernel.invoke_function_call(
            function_call=tool_call_mock,
            chat_history=chat_history_mock,
            arguments=arguments,
            function_call_count=1,
            request_index=0,
            function_behavior=FunctionChoiceBehavior.Auto(),
        )


async def test_invoke_function_call_non_allowed_func_throws(kernel: Kernel, get_tool_call_mock):
    tool_call_mock = get_tool_call_mock
    result_mock = MagicMock(spec=ChatMessageContent)
    result_mock.items = [tool_call_mock]
    chat_history_mock = MagicMock(spec=ChatHistory)

    func_mock = AsyncMock(spec=KernelFunction)
    func_meta = KernelFunctionMetadata(name="function", is_prompt=False)
    func_mock.metadata = func_meta
    func_mock.name = "function"
    func_result = FunctionResult(value="Function result", function=func_meta)
    func_mock.invoke = MagicMock(return_value=func_result)

    arguments = KernelArguments()

    with patch("semantic_kernel.kernel.logger", autospec=True):
        await kernel.invoke_function_call(
            function_call=tool_call_mock,
            chat_history=chat_history_mock,
            arguments=arguments,
            function_call_count=1,
            request_index=0,
            function_behavior=FunctionChoiceBehavior.Auto(filters={"included_functions": ["unknown"]}),
        )


async def test_invoke_function_call_no_name_throws(kernel: Kernel, get_tool_call_mock):
    tool_call_mock = get_tool_call_mock
    tool_call_mock.name = None
    result_mock = MagicMock(spec=ChatMessageContent)
    result_mock.items = [tool_call_mock]
    chat_history_mock = MagicMock(spec=ChatHistory)

    func_mock = AsyncMock(spec=KernelFunction)
    func_meta = KernelFunctionMetadata(name="function", is_prompt=False)
    func_mock.metadata = func_meta
    func_mock.name = "function"
    func_result = FunctionResult(value="Function result", function=func_meta)
    func_mock.invoke = MagicMock(return_value=func_result)

    arguments = KernelArguments()

    with (
        patch("semantic_kernel.kernel.logger", autospec=True),
    ):
        await kernel.invoke_function_call(
            function_call=tool_call_mock,
            chat_history=chat_history_mock,
            arguments=arguments,
            function_call_count=1,
            request_index=0,
            function_behavior=FunctionChoiceBehavior.Auto(),
        )


async def test_invoke_function_call_not_enough_parsed_args(kernel: Kernel, get_tool_call_mock):
    tool_call_mock = get_tool_call_mock
    tool_call_mock.to_kernel_arguments.return_value = {}
    result_mock = MagicMock(spec=ChatMessageContent)
    result_mock.items = [tool_call_mock]
    chat_history_mock = MagicMock(spec=ChatHistory)

    func_mock = AsyncMock(spec=KernelFunction)
    func_meta = KernelFunctionMetadata(name="function", is_prompt=False)
    func_mock.metadata = func_meta
    func_mock.name = "function"
    func_mock.parameters = [KernelParameterMetadata(name="param1", is_required=True)]
    func_result = FunctionResult(value="Function result", function=func_meta)
    func_mock.invoke = MagicMock(return_value=func_result)

    arguments = KernelArguments()

    with (
        patch("semantic_kernel.kernel.logger", autospec=True),
        patch("semantic_kernel.kernel.Kernel.get_function", return_value=func_mock),
    ):
        await kernel.invoke_function_call(
            function_call=tool_call_mock,
            chat_history=chat_history_mock,
            arguments=arguments,
            function_call_count=1,
            request_index=0,
            function_behavior=FunctionChoiceBehavior.Auto(),
        )


async def test_invoke_function_call_with_continuation_on_malformed_arguments(kernel: Kernel, get_tool_call_mock):
    tool_call_mock = MagicMock(spec=FunctionCallContent)
    tool_call_mock.to_kernel_arguments.side_effect = FunctionCallInvalidArgumentsException("Malformed arguments")
    tool_call_mock.name = "test-function"
    tool_call_mock.function_name = "function"
    tool_call_mock.plugin_name = "test"
    tool_call_mock.arguments = {"arg_name": "arg_value"}
    tool_call_mock.ai_model_id = None
    tool_call_mock.metadata = {}
    tool_call_mock.index = 0
    tool_call_mock.to_kernel_arguments.return_value = {"arg_name": "arg_value"}
    tool_call_mock.id = "test_id"
    result_mock = MagicMock(spec=ChatMessageContent)
    result_mock.items = [tool_call_mock]
    chat_history_mock = MagicMock(spec=ChatHistory)

    func_mock = MagicMock(spec=KernelFunction)
    func_meta = KernelFunctionMetadata(name="function", is_prompt=False)
    func_mock.metadata = func_meta
    func_mock.name = "function"
    func_result = FunctionResult(value="Function result", function=func_meta)
    func_mock.invoke = AsyncMock(return_value=func_result)
    arguments = KernelArguments()

    with patch("semantic_kernel.kernel.logger", autospec=True) as logger_mock:
        await kernel.invoke_function_call(
            function_call=tool_call_mock,
            chat_history=chat_history_mock,
            arguments=arguments,
            function_call_count=1,
            request_index=0,
            function_behavior=FunctionChoiceBehavior.Auto(),
        )

    logger_mock.info.assert_any_call(
        "Received invalid arguments for function test-function: Malformed arguments. Trying tool call again."
    )

    add_message_calls = chat_history_mock.add_message.call_args_list
    assert any(
        call[1]["message"].items[0].result
        == "The tool call arguments are malformed. Arguments must be in JSON format. Please try again."  # noqa: E501
        and call[1]["message"].items[0].id == "test_id"
        and call[1]["message"].items[0].name == "test-function"
        for call in add_message_calls
    ), "Expected call to add_message not found with the expected message content and metadata."


# endregion
# region Plugins


def test_add_plugin_from_directory(kernel: Kernel):
    # import plugins
    plugins_directory = os.path.join(os.path.dirname(__file__), "../../assets", "test_plugins")
    # path to plugins directory
    plugin = kernel.add_plugin(plugin_name="TestPlugin", parent_directory=plugins_directory)
    assert plugin is not None
    assert len(plugin.functions) == 2
    func = plugin.functions["TestFunction"]
    assert func is not None
    func_handlebars = plugin.functions["TestFunctionHandlebars"]
    assert func_handlebars is not None


def test_plugin_no_plugin(kernel: Kernel):
    with pytest.raises(ValueError):
        kernel.add_plugin(plugin_name="test")


def test_plugin_name_from_class_name(kernel: Kernel):
    kernel.add_plugin(" ", None)
    assert "str" in kernel.plugins


def test_plugin_name_from_name_attribute(kernel: Kernel):
    @dataclass
    class TestPlugin:
        name: str = "test_plugin"

    kernel.add_plugin(TestPlugin(), None)
    assert "test_plugin" in kernel.plugins


def test_plugin_name_not_string_error(kernel: Kernel):
    with pytest.raises(TypeError):
        kernel.add_plugin(" ", plugin_name=Path(__file__).parent)


def test_plugins_add_plugins(kernel: Kernel):
    plugin1 = KernelPlugin(name="TestPlugin")
    plugin2 = KernelPlugin(name="TestPlugin2")

    kernel.add_plugins([plugin1, plugin2])
    assert len(kernel.plugins) == 2


def test_add_function_from_prompt(kernel: Kernel):
    prompt = """
    Write a short story about two Corgis on an adventure.
    The story must be:
    - G rated
    - Have a positive message
    - No sexism, racism or other bias/bigotry
    - Be exactly {{$paragraph_count}} paragraphs long
    - Be written in this language: {{$language}}
    - The two names of the corgis are {{GenerateNames.generate_names}}
    """

    kernel.add_function(
        prompt=prompt,
        function_name="TestFunction",
        plugin_name="TestPlugin",
        description="Write a short story.",
        execution_settings=PromptExecutionSettings(
            extension_data={"max_tokens": 500, "temperature": 0.5, "top_p": 0.5}
        ),
    )
    func = kernel.get_function("TestPlugin", "TestFunction")
    assert func.name == "TestFunction"
    assert func.description == "Write a short story."
    assert len(func.parameters) == 2


def test_add_function_not_provided(kernel: Kernel):
    with pytest.raises(ValueError):
        kernel.add_function(function_name="TestFunction", plugin_name="TestPlugin")


def test_add_function_from_prompt_different_values(kernel: Kernel):
    template = """
    Write a short story about two Corgis on an adventure.
    The story must be:
    - G rated
    - Have a positive message
    - No sexism, racism or other bias/bigotry
    - Be exactly {{$paragraph_count}} paragraphs long
    - Be written in this language: {{$language}}
    - The two names of the corgis are {{GenerateNames.generate_names}}
    """
    prompt = "test"

    kernel.add_function(
        prompt=prompt,
        function_name="TestFunction",
        plugin_name="TestPlugin",
        description="Write a short story.",
        template_format="handlebars",
        prompt_template_config=PromptTemplateConfig(
            template=template,
        ),
        execution_settings=PromptExecutionSettings(
            extension_data={"max_tokens": 500, "temperature": 0.5, "top_p": 0.5}
        ),
    )
    func = kernel.get_function("TestPlugin", "TestFunction")
    assert func.name == "TestFunction"
    assert func.description == "Write a short story."
    assert isinstance(func.prompt_template, KernelPromptTemplate)
    assert len(func.parameters) == 2


def test_add_functions(kernel: Kernel):
    @kernel_function(name="func1")
    def func1(arg1: str) -> str:
        return "test"

    @kernel_function(name="func2")
    def func2(arg1: str) -> str:
        return "test"

    plugin = kernel.add_functions(plugin_name="test", functions=[func1, func2])
    assert len(plugin.functions) == 2


def test_add_functions_to_existing(kernel: Kernel):
    kernel.add_plugin(KernelPlugin(name="test"))

    @kernel_function(name="func1")
    def func1(arg1: str) -> str:
        return "test"

    @kernel_function(name="func2")
    def func2(arg1: str) -> str:
        return "test"

    plugin = kernel.add_functions(plugin_name="test", functions=[func1, func2])
    assert len(plugin.functions) == 2


def test_import_plugin_from_openapi(kernel: Kernel):
    openapi_spec_file = os.path.join(
        os.path.dirname(__file__), "../../assets/test_plugins", "TestOpenAPIPlugin", "akv-openapi.yaml"
    )

    kernel.add_plugin_from_openapi(
        plugin_name="TestOpenAPIPlugin",
        openapi_document_path=openapi_spec_file,
    )
    plugin = kernel.get_plugin(plugin_name="TestOpenAPIPlugin")
    assert plugin is not None
    assert plugin.name == "TestOpenAPIPlugin"
    assert plugin.functions.get("GetSecret") is not None
    assert plugin.functions.get("SetSecret") is not None


def test_get_plugin(kernel: Kernel):
    kernel.add_plugin(KernelPlugin(name="TestPlugin"))
    plugin = kernel.get_plugin("TestPlugin")
    assert plugin is not None


def test_get_plugin_not_found(kernel: Kernel):
    with pytest.raises(KernelPluginNotFoundError):
        kernel.get_plugin("TestPlugin2")


def test_get_function(kernel: Kernel, custom_plugin_class):
    kernel.add_plugin(custom_plugin_class(), "TestPlugin")
    func = kernel.get_function("TestPlugin", "getLightStatus")
    assert func


def test_func_plugin_not_found(kernel: Kernel):
    with pytest.raises(KernelPluginNotFoundError):
        kernel.get_function("TestPlugin", "TestFunction")


def test_func_function_not_found(kernel: Kernel, custom_plugin_class):
    kernel.add_plugin(custom_plugin_class(), "TestPlugin")
    with pytest.raises(KernelFunctionNotFoundError):
        kernel.get_function("TestPlugin", "TestFunction")


def test_get_function_from_fqn(kernel: Kernel, custom_plugin_class):
    kernel.add_plugin(custom_plugin_class(), "TestPlugin")
    func = kernel.get_function_from_fully_qualified_function_name("TestPlugin-getLightStatus")
    assert func


def test_get_function_from_fqn_wo_plugin(kernel: Kernel, custom_plugin_class):
    kernel.add_plugin(custom_plugin_class(), "TestPlugin")
    func = kernel.get_function_from_fully_qualified_function_name("getLightStatus")
    assert func


# endregion
# region Services


def test_kernel_add_service(kernel: Kernel, service: AIServiceClientBase):
    kernel.add_service(service)
    assert kernel.services == {"service": service}


def test_kernel_add_service_twice(kernel_with_service: Kernel, service: AIServiceClientBase):
    with pytest.raises(KernelFunctionAlreadyExistsError):
        kernel_with_service.add_service(service)
    assert kernel_with_service.services == {"service": service}


def test_kernel_add_multiple_services(kernel_with_service: Kernel, service: AIServiceClientBase):
    service2 = AIServiceClientBase(service_id="service2", ai_model_id="ai_model_id")
    kernel_with_service.add_service(service2)
    assert kernel_with_service.services["service2"] == service2
    assert len(kernel_with_service.services) == 2


def test_kernel_remove_service(kernel_with_service: Kernel):
    kernel_with_service.remove_service("service")
    assert kernel_with_service.services == {}


def test_kernel_remove_service_error(kernel_with_service: Kernel):
    with pytest.raises(KernelServiceNotFoundError):
        kernel_with_service.remove_service("service2")


def test_kernel_remove_all_service(kernel_with_service: Kernel):
    kernel_with_service.remove_all_services()
    assert kernel_with_service.services == {}


def test_get_default_service(kernel_with_default_service: Kernel):
    service_get = kernel_with_default_service.get_service()
    assert service_get == kernel_with_default_service.services["default"]


def test_get_default_service_with_type(kernel_with_default_service: Kernel):
    service_get = kernel_with_default_service.get_service(type=AIServiceClientBase)
    assert service_get == kernel_with_default_service.services["default"]


def test_get_service(kernel_with_service: Kernel):
    service_get = kernel_with_service.get_service("service")
    assert service_get == kernel_with_service.services["service"]


def test_get_service_by_type(kernel_with_service: Kernel):
    service_get = kernel_with_service.get_service(type=AIServiceClientBase)
    assert service_get == kernel_with_service.services["service"]


def test_get_service_by_type_not_found(kernel_with_service: Kernel):
    with pytest.raises(KernelServiceNotFoundError):
        kernel_with_service.get_service(type=ChatCompletionClientBase)


def test_get_default_service_by_type(kernel_with_default_service: Kernel):
    service_get = kernel_with_default_service.get_services_by_type(AIServiceClientBase)
    assert service_get["default"] == kernel_with_default_service.services["default"]


def test_get_services_by_type(kernel_with_service: Kernel):
    service_get = kernel_with_service.get_services_by_type(AIServiceClientBase)
    assert service_get["service"] == kernel_with_service.services["service"]


def test_get_service_with_id_not_found(kernel_with_service: Kernel):
    with pytest.raises(KernelServiceNotFoundError):
        kernel_with_service.get_service("service2", type=AIServiceClientBase)


def test_get_service_with_type(kernel_with_service: Kernel):
    service_get = kernel_with_service.get_service("service", type=AIServiceClientBase)
    assert service_get == kernel_with_service.services["service"]


def test_get_service_with_multiple_types(kernel_with_service: Kernel):
    service_get = kernel_with_service.get_service("service", type=(AIServiceClientBase, ChatCompletionClientBase))
    assert service_get == kernel_with_service.services["service"]


def test_get_service_with_multiple_types_union(kernel_with_service: Kernel):
    """This is valid syntax only in python 3.10+. It is skipped for older versions."""
    service_get = kernel_with_service.get_service("service", type=Union[AIServiceClientBase, ChatCompletionClientBase])
    assert service_get == kernel_with_service.services["service"]


def test_get_service_with_type_not_found(kernel_with_service: Kernel):
    with pytest.raises(KernelServiceNotFoundError):
        kernel_with_service.get_service("service", type=ChatCompletionClientBase)


def test_get_service_no_id(kernel_with_service: Kernel):
    service_get = kernel_with_service.get_service()
    assert service_get == kernel_with_service.services["service"]


def test_instantiate_prompt_execution_settings_through_kernel(kernel_with_service: Kernel):
    settings = kernel_with_service.get_prompt_execution_settings_from_service_id("service")
    assert settings.service_id == "service"


# endregion
# region experimental class decorator


def test_experimental_class_has_decorator_and_flag(experimental_plugin_class):
    assert hasattr(experimental_plugin_class, "is_experimental")
    assert experimental_plugin_class.is_experimental
    assert "This class is marked as 'experimental' and may change in the future" in experimental_plugin_class.__doc__


# endregion

# region copy and clone


def test_kernel_model_dump(
    kernel: Kernel,
    custom_plugin_class: type,
    auto_function_invocation_filter: Callable,
):
    kernel.add_plugin(custom_plugin_class(), "TestPlugin")
    kernel.add_filter(FilterTypes.AUTO_FUNCTION_INVOCATION, auto_function_invocation_filter)

    kernel_dict = kernel.model_dump()

    assert kernel_dict is not None
    assert kernel_dict["plugins"] is not None and len(kernel_dict["plugins"]) > 0
    assert (
        kernel_dict["auto_function_invocation_filters"] is not None
        and len(kernel_dict["auto_function_invocation_filters"]) > 0
    )


def test_kernel_deep_copy(
    kernel: Kernel,
    custom_plugin_class: type,
    auto_function_invocation_filter: Callable,
):
    kernel.add_plugin(custom_plugin_class(), "TestPlugin")
    kernel.add_filter(FilterTypes.AUTO_FUNCTION_INVOCATION, auto_function_invocation_filter)

    kernel_copy = kernel.model_copy(deep=True)

    assert kernel_copy is not None
    assert kernel_copy.plugins is not None and len(kernel_copy.plugins) > 0
    assert (
        kernel_copy.auto_function_invocation_filters is not None
        and len(kernel_copy.auto_function_invocation_filters) > 0
    )


def test_kernel_model_dump_fail_with_services(kernel: Kernel):
    open_ai_chat_completion = OpenAIChatCompletion(ai_model_id="abc", api_key="abc")
    kernel.add_service(open_ai_chat_completion)

    with pytest.raises(TypeError):
        # This will fail because OpenAIChatCompletion is not serializable, more specifically,
        # the client is not serializable
        kernel.model_dump(deep=True)


def test_kernel_deep_copy_fail_with_services(kernel: Kernel):
    open_ai_chat_completion = OpenAIChatCompletion(ai_model_id="abc", api_key="abc")
    kernel.add_service(open_ai_chat_completion)

    with pytest.raises(TypeError):
        # This will fail because OpenAIChatCompletion is not serializable, more specifically,
        # the client is not serializable
        kernel.model_copy(deep=True)


def test_kernel_clone(
    kernel: Kernel,
    custom_plugin_class: type,
    auto_function_invocation_filter: Callable,
):
    kernel.add_service(OpenAIChatCompletion(ai_model_id="abc", api_key="abc"))
    kernel.add_plugin(custom_plugin_class(), "TestPlugin")
    kernel.add_filter(FilterTypes.AUTO_FUNCTION_INVOCATION, auto_function_invocation_filter)

    kernel_clone = kernel.clone()

    # Assert the clone has all the same properties as the original kernel
    assert kernel_clone is not None
    assert kernel_clone.plugins is not None and len(kernel_clone.plugins) > 0
    assert (
        kernel_clone.auto_function_invocation_filters is not None
        and len(kernel_clone.auto_function_invocation_filters) > 0
    )
    assert kernel_clone.services is not None and len(kernel_clone.services) > 0

    # Assert the clone is a deep copy
    kernel_clone.plugins["TestPlugin"].functions["getLightStatus"].metadata.name = "getLightStatus2"
    assert kernel.plugins["TestPlugin"].functions["getLightStatus"].metadata.name == "getLightStatus"

    kernel_clone.plugins.clear()
    kernel_clone.remove_filter(filter_type=FilterTypes.AUTO_FUNCTION_INVOCATION, position=0)
    kernel_clone.remove_all_services()

    assert kernel.plugins is not None and len(kernel.plugins) > 0
    assert kernel.auto_function_invocation_filters is not None and len(kernel.auto_function_invocation_filters) > 0
    assert kernel.services is not None and len(kernel.services) > 0


# endregion
