# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

import os
import sys
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from pydantic import ValidationError

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.connectors.openai_plugin.openai_function_execution_parameters import (
    OpenAIFunctionExecutionParameters,
)
from semantic_kernel.events.function_invoked_event_args import FunctionInvokedEventArgs
from semantic_kernel.events.function_invoking_event_args import FunctionInvokingEventArgs
from semantic_kernel.exceptions import (
    FunctionInitializationError,
    KernelFunctionAlreadyExistsError,
    KernelServiceNotFoundError,
    ServiceInvalidTypeError,
)
from semantic_kernel.exceptions.function_exceptions import (
    FunctionNameNotUniqueError,
    PluginInitializationError,
    PluginInvalidNameError,
)
from semantic_kernel.exceptions.kernel_exceptions import KernelFunctionNotFoundError, KernelPluginNotFoundError
from semantic_kernel.exceptions.template_engine_exceptions import TemplateSyntaxError
from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.functions.kernel_plugin_collection import KernelPluginCollection
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
    assert kernel.function_invoked_handlers is not None
    assert kernel.function_invoking_handlers is not None


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
    plugins = KernelPluginCollection()
    kernel = Kernel(plugins=plugins)
    assert kernel.plugins is not None


# endregion
# region Invoke Functions


@pytest.mark.asyncio
@pytest.mark.parametrize("pipeline_count", [1, 2, 3])
async def test_invoke_functions(kernel: Kernel, pipeline_count: int, create_mock_function):
    mock_function = create_mock_function(name="test_function")
    kernel.plugins.add(KernelPlugin(name="test", functions=[mock_function]))
    functions = [mock_function] * pipeline_count

    await kernel.invoke(functions, KernelArguments())

    assert mock_function.invoke.call_count == pipeline_count


@pytest.mark.asyncio
async def test_invoke_functions_by_name(kernel: Kernel, create_mock_function):
    mock_function = create_mock_function(name="test_function")
    kernel.plugins.add(KernelPlugin(name="test", functions=[mock_function]))

    await kernel.invoke(function_name="test_function", plugin_name="test", arguments=KernelArguments())

    assert mock_function.invoke.call_count == 1

    async for response in kernel.invoke_stream(function_name="test_function", plugin_name="test"):
        assert response[0].text == "test"


@pytest.mark.asyncio
async def test_invoke_functions_fail(kernel: Kernel, create_mock_function):
    mock_function = create_mock_function(name="test_function")
    kernel.plugins.add(KernelPlugin(name="test", functions=[mock_function]))

    with pytest.raises(KernelFunctionNotFoundError):
        await kernel.invoke(arguments=KernelArguments())

    with pytest.raises(KernelFunctionNotFoundError):
        async for _ in kernel.invoke_stream(arguments=KernelArguments()):
            pass


@pytest.mark.asyncio
@pytest.mark.parametrize("pipeline_count", [1, 2, 3])
async def test_invoke_stream_functions(kernel: Kernel, pipeline_count: int, create_mock_function):
    mock_function = create_mock_function(name="test_function")
    kernel.plugins.add(KernelPlugin(name="test", functions=[mock_function]))
    functions = [mock_function] * pipeline_count

    async for part in kernel.invoke_stream(functions, input="test"):
        assert part[0].text == "test"

    assert mock_function.invoke.call_count == pipeline_count - 1


@pytest.mark.asyncio
async def test_invoke_stream_functions_throws_exception(kernel: Kernel, create_mock_function):
    mock_function = create_mock_function(name="test_function")
    kernel.plugins.add(KernelPlugin(name="test", functions=[mock_function]))
    functions = [mock_function]

    function_result_with_exception = FunctionResult(
        value="", function=mock_function.metadata, output=None, metadata={"exception": "Test Exception"}
    )

    with patch("semantic_kernel.kernel.Kernel.invoke_stream", return_value=AsyncMock()) as mocked_invoke_stream:
        mocked_invoke_stream.return_value.__aiter__.return_value = [function_result_with_exception]

        async for part in kernel.invoke_stream(functions, input="test"):
            assert "exception" in part.metadata, "Expected exception metadata in the FunctionResult."
            assert part.metadata["exception"] == "Test Exception", "The exception message does not match."
            break


@pytest.mark.asyncio
async def test_invoke_prompt(kernel: Kernel, create_mock_function):
    mock_function = create_mock_function(name="test_function")
    with patch(
        "semantic_kernel.functions.kernel_function_from_prompt.KernelFunctionFromPrompt._invoke_internal"
    ) as mock_invoke:
        mock_invoke.return_value = mock_function.invoke.return_value
        await kernel.invoke_prompt(prompt="test", plugin_name="test", function_name="test", arguments=KernelArguments())
        mock_invoke.assert_called_once()


@pytest.mark.asyncio
async def test_invoke_prompt_no_prompt_error(kernel: Kernel):
    with pytest.raises(TemplateSyntaxError):
        await kernel.invoke_prompt(
            function_name="test_function",
            plugin_name="test_plugin",
            prompt="",
        )


# endregion
# region Function Invoking/Invoked Events


def test_invoke_handles_register(kernel_with_handlers: Kernel):
    assert len(kernel_with_handlers.function_invoking_handlers) == 1
    assert len(kernel_with_handlers.function_invoked_handlers) == 1


def test_invoke_handles_remove(kernel_with_handlers: Kernel):
    assert len(kernel_with_handlers.function_invoking_handlers) == 1
    assert len(kernel_with_handlers.function_invoked_handlers) == 1

    invoking_handler = list(kernel_with_handlers.function_invoking_handlers.values())[0]
    invoked_handler = list(kernel_with_handlers.function_invoked_handlers.values())[0]

    kernel_with_handlers.remove_function_invoking_handler(invoking_handler)
    kernel_with_handlers.remove_function_invoked_handler(invoked_handler)

    assert len(kernel_with_handlers.function_invoking_handlers) == 0
    assert len(kernel_with_handlers.function_invoked_handlers) == 0


@pytest.mark.asyncio
@pytest.mark.parametrize("pipeline_count", [1, 2])
async def test_invoke_handles_pre_invocation(kernel: Kernel, pipeline_count: int, create_mock_function):
    mock_function = create_mock_function(name="test_function")
    kernel.plugins.add(KernelPlugin(name="test", functions=[mock_function]))

    invoked = 0

    def invoking_handler(kernel: Kernel, e: FunctionInvokingEventArgs) -> FunctionInvokingEventArgs:
        nonlocal invoked
        invoked += 1
        return e

    kernel.add_function_invoking_handler(invoking_handler)
    functions = [mock_function] * pipeline_count

    # Act
    await kernel.invoke(functions, KernelArguments())

    # Assert
    assert invoked == pipeline_count
    assert mock_function.invoke.call_count == pipeline_count


@pytest.mark.asyncio
async def test_invoke_pre_invocation_skip_dont_trigger_invoked_handler(kernel: Kernel, create_mock_function):
    mock_function1 = create_mock_function(name="SkipMe")
    mock_function2 = create_mock_function(name="DontSkipMe")
    invoked = 0
    invoking = 0
    invoked_function_name = ""

    def invoking_handler(sender, e):
        nonlocal invoking
        invoking += 1
        if e.kernel_function_metadata.name == "SkipMe":
            e.skip()

    def invoked_handler(sender, e):
        nonlocal invoked_function_name, invoked
        invoked_function_name = e.kernel_function_metadata.name
        invoked += 1
        return e

    kernel.add_function_invoking_handler(invoking_handler)
    kernel.add_function_invoked_handler(invoked_handler)

    # Act
    _ = await kernel.invoke([mock_function1, mock_function2], KernelArguments())

    # Assert
    assert invoking == 2
    assert invoked == 1
    assert invoked_function_name == "DontSkipMe"


@pytest.mark.asyncio
@pytest.mark.parametrize("pipeline_count", [1, 2])
async def test_invoke_handles_post_invocation(kernel: Kernel, pipeline_count, create_mock_function):
    mock_function = create_mock_function("test_function")
    invoked = 0

    def invoked_handler(sender, e):
        nonlocal invoked
        invoked += 1
        return e

    kernel.add_function_invoked_handler(invoked_handler)
    functions = [mock_function] * pipeline_count

    # Act
    _ = await kernel.invoke(functions, KernelArguments())

    # Assert
    assert invoked == pipeline_count
    mock_function.invoke.assert_called()
    assert mock_function.invoke.call_count == pipeline_count


@pytest.mark.asyncio
async def test_invoke_post_invocation_repeat_is_working(kernel: Kernel, create_mock_function):
    mock_function = create_mock_function(name="RepeatMe")
    invoked = 0
    repeat_times = 0

    def invoked_handler(sender, e):
        nonlocal invoked, repeat_times
        invoked += 1

        if repeat_times < 3:
            e.repeat()
            repeat_times += 1
        return e

    kernel.add_function_invoked_handler(invoked_handler)

    # Act
    _ = await kernel.invoke(mock_function)

    # Assert
    assert invoked == 4
    assert repeat_times == 3


@pytest.mark.asyncio
async def test_invoke_change_variable_invoking_handler(kernel: Kernel, create_mock_function):
    original_input = "Importance"
    new_input = "Problems"

    mock_function = create_mock_function(name="test_function", value=new_input)

    def invoking_handler(sender, e: FunctionInvokingEventArgs):
        e.arguments["input"] = new_input
        e.updated_arguments = True
        return e

    kernel.add_function_invoking_handler(invoking_handler)
    arguments = KernelArguments(input=original_input)
    # Act
    result = await kernel.invoke([mock_function], arguments)

    # Assert
    assert str(result) == new_input
    assert arguments["input"] == new_input


@pytest.mark.asyncio
async def test_invoke_change_variable_invoked_handler(kernel: Kernel, create_mock_function):
    original_input = "Importance"
    new_input = "Problems"

    mock_function = create_mock_function(name="test_function", value=new_input)

    def invoked_handler(sender, e: FunctionInvokedEventArgs):
        e.arguments["input"] = new_input
        e.updated_arguments = True
        return e

    kernel.add_function_invoked_handler(invoked_handler)
    arguments = KernelArguments(input=original_input)

    # Act
    result = await kernel.invoke(mock_function, arguments)

    # Assert
    assert str(result) == new_input
    assert arguments["input"] == new_input


# endregion
# region Plugins


def test_prompt_plugin_can_be_imported(kernel: Kernel):
    # import plugins
    plugins_directory = os.path.join(os.path.dirname(__file__), "../../assets", "test_plugins")
    # path to plugins directory
    plugin = kernel.import_plugin_from_prompt_directory(plugins_directory, "TestPlugin")

    assert plugin is not None
    assert len(plugin.functions) == 2
    func = plugin.functions["TestFunction"]
    assert func is not None
    func_handlebars = plugin.functions["TestFunctionHandlebars"]
    assert func_handlebars is not None


def test_prompt_plugin_not_found(kernel: Kernel):
    # import plugins
    plugins_directory = os.path.join(os.path.dirname(__file__), "../../assets", "test_plugins_fail")
    # path to plugins directory
    with pytest.raises(PluginInitializationError):
        kernel.import_plugin_from_prompt_directory(plugins_directory, "TestPlugin")


def test_plugin_name_error(kernel: Kernel):
    with pytest.raises(PluginInvalidNameError):
        kernel.import_plugin_from_object(None, " ")


def test_native_plugin_can_be_imported(kernel: Kernel):
    # import plugins
    plugins_directory = os.path.join(os.path.dirname(__file__), "../../assets", "test_native_plugins")
    # path to plugins directory
    plugin = kernel.import_native_plugin_from_directory(plugins_directory, "TestNativePlugin")

    assert plugin is not None
    assert len(plugin.functions) == 1
    assert plugin.functions.get("echoAsync") is not None
    plugin_config = plugin.functions["echoAsync"]
    assert plugin_config.name == "echoAsync"
    assert plugin_config.description == "Echo for input text"


def test_native_plugin_cannot_be_imported(kernel: Kernel):
    # import plugins
    plugins_directory = os.path.join(os.path.dirname(__file__), "../../assets", "test_native_plugins")
    # path to plugins directory
    plugin = kernel.import_native_plugin_from_directory(plugins_directory, "TestNativePluginNoClass")

    assert not plugin


def test_native_plugin_not_found(kernel: Kernel):
    # import plugins
    plugins_directory = os.path.join(os.path.dirname(__file__), "../../assets", "test_native_plugins_fail")
    # path to plugins directory
    with pytest.raises(PluginInitializationError):
        kernel.import_native_plugin_from_directory(plugins_directory, "TestNativePlugin")


def test_plugin_from_object_dict(kernel: Kernel, decorated_native_function):
    plugin_obj = {"getLightStatusFunc": decorated_native_function}
    plugin = kernel.import_plugin_from_object(plugin_obj, "TestPlugin")

    assert plugin is not None
    assert len(plugin.functions) == 1
    assert plugin.functions.get("getLightStatus") is not None


def test_plugin_from_object_custom_class(kernel: Kernel, custom_plugin_class):
    plugin = kernel.import_plugin_from_object(custom_plugin_class(), "TestPlugin")

    assert plugin is not None
    assert len(plugin.functions) == 1
    assert plugin.functions.get("getLightStatus") is not None


def test_plugin_from_object_custom_class_name_not_unique(kernel: Kernel, custom_plugin_class):
    plugin_obj = custom_plugin_class()
    plugin_obj.decorated_native_function_2 = plugin_obj.decorated_native_function
    with pytest.raises(FunctionNameNotUniqueError):
        kernel.import_plugin_from_object(plugin_obj, "TestPlugin")


def test_create_function_from_prompt_succeeds(kernel: Kernel):
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

    func = kernel.create_function_from_prompt(
        prompt=prompt,
        function_name="TestFunction",
        plugin_name="TestPlugin",
        description="Write a short story.",
        execution_settings=PromptExecutionSettings(
            extension_data={"max_tokens": 500, "temperature": 0.5, "top_p": 0.5}
        ),
    )
    assert func.name == "TestFunction"
    assert func.description == "Write a short story."
    assert len(func.parameters) == 2


def test_create_function_from_yaml_empty_string(kernel: Kernel):
    with pytest.raises(PluginInitializationError):
        kernel.create_function_from_yaml("", "plugin_name")


def test_create_function_from_yaml_malformed_string(kernel: Kernel):
    with pytest.raises(PluginInitializationError):
        kernel.create_function_from_yaml("not yaml dict", "plugin_name")


def test_create_function_from_valid_yaml(kernel: Kernel):
    plugins_directory = os.path.join(os.path.dirname(__file__), "../../assets/test_plugins", "TestPlugin")

    plugin = kernel.import_plugin_from_prompt_directory(plugins_directory, "TestFunctionYaml")
    assert plugin is not None


def test_create_function_from_valid_yaml_handlebars(kernel: Kernel):
    plugins_directory = os.path.join(os.path.dirname(__file__), "../../assets/test_plugins", "TestPlugin")

    plugin = kernel.import_plugin_from_prompt_directory(plugins_directory, "TestFunctionYamlHandlebars")
    assert plugin is not None
    assert plugin["TestFunctionHandlebars"] is not None


def test_create_function_from_valid_yaml_jinja2(kernel: Kernel):
    plugins_directory = os.path.join(os.path.dirname(__file__), "../../assets/test_plugins", "TestPlugin")

    plugin = kernel.import_plugin_from_prompt_directory(plugins_directory, "TestFunctionYamlJinja2")
    assert plugin is not None
    assert plugin["TestFunctionJinja2"] is not None


@pytest.mark.asyncio
@patch("semantic_kernel.connectors.openai_plugin.openai_utils.OpenAIUtils.parse_openai_manifest_for_openapi_spec_url")
async def test_import_openai_plugin_from_file(mock_parse_openai_manifest, kernel: Kernel):
    openai_spec_file = os.path.join(os.path.dirname(__file__), "../../assets/test_plugins", "TestPlugin")
    with open(os.path.join(openai_spec_file, "TestOpenAIPlugin", "akv-openai.json"), "r") as file:
        openai_spec = file.read()

    openapi_spec_file_path = os.path.join(
        os.path.dirname(__file__), "../../assets/test_plugins", "TestPlugin", "TestOpenAPIPlugin", "akv-openapi.yaml"
    )
    mock_parse_openai_manifest.return_value = openapi_spec_file_path

    plugin = await kernel.import_plugin_from_openai(
        plugin_name="TestOpenAIPlugin",
        plugin_str=openai_spec,
        execution_parameters=OpenAIFunctionExecutionParameters(
            http_client=AsyncMock(),
            auth_callback=AsyncMock(),
            server_url_override="http://localhost",
            enable_dynamic_payload=True,
        ),
    )
    assert plugin is not None
    assert plugin.name == "TestOpenAIPlugin"
    assert plugin.functions.get("GetSecret") is not None
    assert plugin.functions.get("SetSecret") is not None


@pytest.mark.asyncio
@patch("httpx.AsyncClient.get")
@patch("semantic_kernel.connectors.openai_plugin.openai_utils.OpenAIUtils.parse_openai_manifest_for_openapi_spec_url")
async def test_import_openai_plugin_from_url(mock_parse_openai_manifest, mock_get, kernel: Kernel):
    openai_spec_file_path = os.path.join(
        os.path.dirname(__file__), "../../assets/test_plugins", "TestPlugin", "TestOpenAIPlugin", "akv-openai.json"
    )
    with open(openai_spec_file_path, "r") as file:
        openai_spec = file.read()

    openapi_spec_file_path = os.path.join(
        os.path.dirname(__file__), "../../assets/test_plugins", "TestPlugin", "TestOpenAPIPlugin", "akv-openapi.yaml"
    )
    mock_parse_openai_manifest.return_value = openapi_spec_file_path

    request = httpx.Request(method="GET", url="http://fake-url.com/akv-openai.json")

    response = httpx.Response(200, text=openai_spec, request=request)
    mock_get.return_value = response

    fake_plugin_url = "http://fake-url.com/akv-openai.json"
    plugin = await kernel.import_plugin_from_openai(
        plugin_name="TestOpenAIPlugin",
        plugin_url=fake_plugin_url,
        execution_parameters=OpenAIFunctionExecutionParameters(
            auth_callback=AsyncMock(),
            server_url_override="http://localhost",
            enable_dynamic_payload=True,
        ),
    )

    assert plugin is not None
    assert plugin.name == "TestOpenAIPlugin"
    assert plugin.functions.get("GetSecret") is not None
    assert plugin.functions.get("SetSecret") is not None

    mock_get.assert_awaited_once_with(fake_plugin_url, headers={"User-Agent": "Semantic-Kernel"})


def test_import_plugin_from_openapi(kernel: Kernel):
    openapi_spec_file = os.path.join(
        os.path.dirname(__file__), "../../assets/test_plugins", "TestPlugin", "TestOpenAPIPlugin", "akv-openapi.yaml"
    )

    plugin = kernel.import_plugin_from_openapi(
        plugin_name="TestOpenAPIPlugin",
        openapi_document_path=openapi_spec_file,
    )

    assert plugin is not None
    assert plugin.name == "TestOpenAPIPlugin"
    assert plugin.functions.get("GetSecret") is not None
    assert plugin.functions.get("SetSecret") is not None


def test_import_plugin_from_openapi_missing_document_throws(kernel: Kernel):
    with pytest.raises(PluginInitializationError):
        kernel.import_plugin_from_openapi(
            plugin_name="TestOpenAPIPlugin",
            openapi_document_path=None,
        )


# endregion
# region Functions


def test_func(kernel: Kernel, custom_plugin_class):
    kernel.import_plugin_from_object(custom_plugin_class(), "TestPlugin")
    func = kernel.func("TestPlugin", "getLightStatus")
    assert func


def test_func_plugin_not_found(kernel: Kernel):
    with pytest.raises(KernelPluginNotFoundError):
        kernel.func("TestPlugin", "TestFunction")


def test_func_function_not_found(kernel: Kernel, custom_plugin_class):
    kernel.import_plugin_from_object(custom_plugin_class(), "TestPlugin")
    with pytest.raises(KernelFunctionNotFoundError):
        kernel.func("TestPlugin", "TestFunction")


@pytest.mark.asyncio
async def test_register_valid_native_function(kernel: Kernel, decorated_native_function):
    registered_func = kernel.register_function_from_method("TestPlugin", decorated_native_function)

    assert isinstance(registered_func, KernelFunction)
    assert kernel.plugins["TestPlugin"]["getLightStatus"] == registered_func
    func_result = await registered_func.invoke(kernel, KernelArguments(arg1="testtest"))
    assert str(func_result) == "test"


def test_register_undecorated_native_function(kernel: Kernel, not_decorated_native_function):
    with pytest.raises(FunctionInitializationError):
        kernel.register_function_from_method("TestPlugin", not_decorated_native_function)


def test_register_with_none_plugin_name(kernel: Kernel, decorated_native_function):
    with pytest.raises(ValidationError):
        kernel.register_function_from_method(method=decorated_native_function, plugin_name=None)


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


@pytest.mark.skipif(sys.version_info < (3, 10), reason="This is valid syntax only in python 3.10+.")
def test_get_service_with_multiple_types_union(kernel_with_service: Kernel):
    """This is valid syntax only in python 3.10+. It is skipped for older versions."""
    service_get = kernel_with_service.get_service("service", type=AIServiceClientBase | ChatCompletionClientBase)
    assert service_get == kernel_with_service.services["service"]


def test_get_service_with_type_not_found(kernel_with_service: Kernel):
    with pytest.raises(ServiceInvalidTypeError):
        kernel_with_service.get_service("service", type=ChatCompletionClientBase)


def test_get_service_no_id(kernel_with_service: Kernel):
    service_get = kernel_with_service.get_service()
    assert service_get == kernel_with_service.services["service"]


def test_instantiate_prompt_execution_settings_through_kernel(kernel_with_service: Kernel):
    settings = kernel_with_service.get_prompt_execution_settings_from_service_id("service")
    assert settings.service_id == "service"


# endregion
