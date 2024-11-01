# Copyright (c) Microsoft. All rights reserved.

import contextlib
import datetime
import json
import logging
import os

import httpx
import pytest
from openai import AsyncOpenAI

from semantic_kernel.connectors.ai.open_ai import OpenAIChatCompletion
from semantic_kernel.connectors.ai.open_ai.settings.open_ai_settings import OpenAISettings
from semantic_kernel.connectors.openapi_plugin import OpenAPIFunctionExecutionParameters
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.functions.kernel_function_from_method import KernelFunctionFromMethod
from semantic_kernel.functions.kernel_function_from_prompt import KernelFunctionFromPrompt
from semantic_kernel.kernel import Kernel

logger = logging.getLogger(__name__)

# region Test Prompts

simple_prompt = "Can you help me tell the time in Seattle right now?"
sk_simple_prompt = "Can you help me tell the time in {{$city}} right now?"
hb_simple_prompt = "Can you help me tell the time in {{city}} right now?"
j2_simple_prompt = "Can you help me tell the time in {{city}} right now?"
sk_prompt = '<message role="system">The current time is {{Time.Now}}</message><message role="user">Can you help me tell the time in {{$city}} right now?</message>'  # noqa: E501
hb_prompt = '<message role="system">The current time is {{Time-Now}}</message><message role="user">Can you help me tell the time in {{city}} right now?</message>'  # noqa: E501
j2_prompt = '<message role="system">The current time is {{Time_Now()}}</message><message role="user">Can you help me tell the time in {{city}} right now?</message>'  # noqa: E501

# endregion

# region Custom Logging Class


class LoggingTransport(httpx.AsyncBaseTransport):
    def __init__(self, inner: httpx.AsyncBaseTransport):
        self.inner = inner
        self.request_content = None

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        logger.info(f"Request: {request.method} {request.url}")
        if request.content:
            self.request_content = request.content.decode("utf-8")
            logger.info(f"Request Body: {self.request_content}")
        elif request.stream:
            stream_content = await request.stream.aread()
            self.request_content = stream_content.decode("utf-8")
            logger.info(f"Request Stream Content: {self.request_content}")
            request.stream = httpx.AsyncByteStream(stream_content)

        return await self.inner.handle_async_request(request)


class LoggingAsyncClient(httpx.AsyncClient):
    def __init__(self, *args, **kwargs):
        transport = kwargs.pop("transport", None)
        self.logging_transport = LoggingTransport(transport or httpx.AsyncHTTPTransport())
        super().__init__(*args, **kwargs, transport=self.logging_transport)

    def get_request_content(self):
        return self.logging_transport.request_content


# endregion

# region Test Helper Methods


def get_new_client():
    openai_settings = OpenAISettings.create()
    logging_async_client = LoggingAsyncClient()
    async_client = AsyncOpenAI(api_key=openai_settings.api_key.get_secret_value(), http_client=logging_async_client)
    return async_client, logging_async_client


async def run_prompt(
    kernel: Kernel,
    is_inline: bool = False,
    is_streaming: bool = False,
    template_format: str = None,
    prompt: str = None,
    arguments: KernelArguments = None,
):
    if is_inline:
        if is_streaming:
            try:
                async for _ in kernel.invoke_prompt_stream(
                    function_name="func_test_stream",
                    plugin_name="plugin_test",
                    prompt=prompt,
                    arguments=arguments,
                    template_format=template_format,
                ):
                    pass
            except NotImplementedError:
                pass
        else:
            await kernel.invoke_prompt(
                function_name="func_test",
                plugin_name="plugin_test_stream",
                prompt=prompt,
                arguments=arguments,
                template_format=template_format,
            )
    else:
        function = KernelFunctionFromPrompt(
            function_name="test_func", plugin_name="test_plugin", prompt=prompt, template_format=template_format
        )
        await run_function(kernel, is_streaming, function=function, arguments=arguments)


async def run_function(
    kernel: Kernel, is_streaming: bool = False, function: KernelFunction = None, arguments: KernelArguments = None
):
    if is_streaming:
        try:
            async for _ in kernel.invoke_stream(function=function, arguments=arguments):
                pass
        except NotImplementedError:
            pass
    else:
        await kernel.invoke(function=function, arguments=arguments)


class City:
    def __init__(self, name):
        self.name = name


# endregion

# region Test Prompt With Chat Roles


@pytest.mark.parametrize(
    "is_inline, is_streaming, template_format, prompt",
    [
        (
            True,
            False,
            "semantic-kernel",
            '<message role="user">Can you help me tell the time in Seattle right now?</message><message role="assistant">Sure! The time in Seattle is currently 3:00 PM.</message><message role="user">What about New York?</message>',  # noqa: E501
        ),
        (
            True,
            True,
            "semantic-kernel",
            '<message role="user">Can you help me tell the time in Seattle right now?</message><message role="assistant">Sure! The time in Seattle is currently 3:00 PM.</message><message role="user">What about New York?</message>',  # noqa: E501
        ),
        (
            False,
            False,
            "semantic-kernel",
            '<message role="user">Can you help me tell the time in Seattle right now?</message><message role="assistant">Sure! The time in Seattle is currently 3:00 PM.</message><message role="user">What about New York?</message>',  # noqa: E501
        ),
        (
            False,
            True,
            "semantic-kernel",
            '<message role="user">Can you help me tell the time in Seattle right now?</message><message role="assistant">Sure! The time in Seattle is currently 3:00 PM.</message><message role="user">What about New York?</message>',  # noqa: E501
        ),
        (
            False,
            False,
            "handlebars",
            '<message role="user">Can you help me tell the time in Seattle right now?</message><message role="assistant">Sure! The time in Seattle is currently 3:00 PM.</message><message role="user">What about New York?</message>',  # noqa: E501
        ),
        (
            False,
            True,
            "handlebars",
            '<message role="user">Can you help me tell the time in Seattle right now?</message><message role="assistant">Sure! The time in Seattle is currently 3:00 PM.</message><message role="user">What about New York?</message>',  # noqa: E501
        ),
        (
            False,
            False,
            "jinja2",
            '<message role="user">Can you help me tell the time in Seattle right now?</message><message role="assistant">Sure! The time in Seattle is currently 3:00 PM.</message><message role="user">What about New York?</message>',  # noqa: E501
        ),
        (
            False,
            True,
            "jinja2",
            '<message role="user">Can you help me tell the time in Seattle right now?</message><message role="assistant">Sure! The time in Seattle is currently 3:00 PM.</message><message role="user">What about New York?</message>',  # noqa: E501
        ),
    ],
)
@pytest.mark.asyncio
async def test_prompt_with_chat_roles(is_inline, is_streaming, template_format, prompt):
    async_client, logging_client = get_new_client()
    ai_service = OpenAIChatCompletion(
        service_id="test",
        ai_model_id="gpt-3.5-turbo",
        async_client=async_client,
    )

    kernel = Kernel()

    kernel.add_service(ai_service)

    await run_prompt(
        kernel=kernel, is_inline=is_inline, is_streaming=is_streaming, template_format=template_format, prompt=prompt
    )

    request_content = logging_client.get_request_content()
    assert request_content is not None

    obtained_object = json.loads(request_content)
    assert obtained_object is not None

    data_directory = os.path.join(os.path.dirname(__file__), "data", "prompt_with_chat_roles_expected.json")
    with open(data_directory) as f:
        expected = f.read()

    expected_object = json.loads(expected)
    assert expected_object is not None

    if is_streaming:
        expected_object["stream"] = True
        expected_object["stream_options"] = {"include_usage": True}

    assert obtained_object == expected_object


# endregion

# region Test Prompt With Complex Objects


@pytest.mark.parametrize(
    "is_inline, is_streaming, template_format, prompt",
    [
        (False, False, "handlebars", "Can you help me tell the time in {{city.name}} right now?"),
        (False, True, "handlebars", "Can you help me tell the time in {{city.name}} right now?"),
        (False, False, "jinja2", "Can you help me tell the time in {{city.name}} right now?"),
        (False, True, "jinja2", "Can you help me tell the time in {{city.name}} right now?"),
        (True, False, "handlebars", "Can you help me tell the time in {{city.name}} right now?"),
        (True, True, "handlebars", "Can you help me tell the time in {{city.name}} right now?"),
        (True, False, "jinja2", "Can you help me tell the time in {{city.name}} right now?"),
        (True, True, "jinja2", "Can you help me tell the time in {{city.name}} right now?"),
    ],
)
@pytest.mark.asyncio
async def test_prompt_with_complex_objects(is_inline, is_streaming, template_format, prompt):
    async_client, logging_client = get_new_client()
    ai_service = OpenAIChatCompletion(
        service_id="default",
        ai_model_id="gpt-3.5-turbo",
        async_client=async_client,
    )

    kernel = Kernel()

    kernel.add_service(ai_service)

    await run_prompt(
        kernel=kernel,
        is_inline=is_inline,
        is_streaming=is_streaming,
        template_format=template_format,
        prompt=prompt,
        arguments=KernelArguments(city=City("Seattle")),
    )

    request_content = logging_client.get_request_content()
    assert request_content is not None

    obtained_object = json.loads(request_content)
    assert obtained_object is not None

    data_directory = os.path.join(os.path.dirname(__file__), "data", "prompt_with_complex_objects_expected.json")
    with open(data_directory) as f:
        expected = f.read()

    expected_object = json.loads(expected)
    assert expected_object is not None

    if is_streaming:
        expected_object["stream"] = True
        expected_object["stream_options"] = {"include_usage": True}

    assert obtained_object == expected_object


# endregion

# region Test Prompt With Helper Functions


@pytest.mark.parametrize(
    "is_inline, is_streaming, template_format, prompt",
    [
        (True, False, "semantic-kernel", sk_prompt),
        (True, True, "semantic-kernel", sk_prompt),
        (False, False, "semantic-kernel", sk_prompt),
        (False, True, "semantic-kernel", sk_prompt),
        (False, False, "handlebars", hb_prompt),
        (False, True, "handlebars", hb_prompt),
        (False, False, "jinja2", j2_prompt),
        (False, True, "jinja2", j2_prompt),
    ],
)
@pytest.mark.asyncio
async def test_prompt_with_helper_functions(is_inline, is_streaming, template_format, prompt):
    async_client, logging_client = get_new_client()
    ai_service = OpenAIChatCompletion(
        service_id="default",
        ai_model_id="gpt-3.5-turbo",
        async_client=async_client,
    )

    kernel = Kernel()

    kernel.add_service(ai_service)

    func = KernelFunctionFromMethod(
        method=kernel_function(
            lambda: datetime.datetime(1989, 6, 4, 12, 11, 13, tzinfo=datetime.timezone.utc).strftime(
                "%a, %d %b %Y %H:%M:%S GMT"
            ),
            name="Now",
        ),
        plugin_name="Time",
    )
    kernel.add_function(plugin_name="Time", function=func)

    await run_prompt(
        kernel=kernel,
        is_inline=is_inline,
        is_streaming=is_streaming,
        template_format=template_format,
        prompt=prompt,
        arguments=KernelArguments(city="Seattle"),
    )

    request_content = logging_client.get_request_content()
    assert request_content is not None

    obtained_object = json.loads(request_content)
    assert obtained_object is not None

    data_directory = os.path.join(os.path.dirname(__file__), "data", "prompt_with_helper_functions_expected.json")
    with open(data_directory) as f:
        expected = f.read()

    expected_object = json.loads(expected)
    assert expected_object is not None

    if is_streaming:
        expected_object["stream"] = True
        expected_object["stream_options"] = {"include_usage": True}

    assert obtained_object == expected_object


# endregion

# region Test Prompt With Simple Variable


@pytest.mark.parametrize(
    "is_inline, is_streaming, template_format, prompt",
    [
        (True, False, "semantic-kernel", sk_simple_prompt),
        (True, True, "semantic-kernel", sk_simple_prompt),
        (False, False, "semantic-kernel", sk_simple_prompt),
        (False, True, "semantic-kernel", sk_simple_prompt),
        (False, False, "handlebars", hb_simple_prompt),
        (False, True, "handlebars", hb_simple_prompt),
        (False, False, "jinja2", j2_simple_prompt),
        (False, True, "jinja2", j2_simple_prompt),
    ],
)
@pytest.mark.asyncio
async def test_prompt_with_simple_variable(is_inline, is_streaming, template_format, prompt):
    async_client, logging_client = get_new_client()
    ai_service = OpenAIChatCompletion(
        service_id="default",
        ai_model_id="gpt-3.5-turbo",
        async_client=async_client,
    )

    kernel = Kernel()

    kernel.add_service(ai_service)

    await run_prompt(
        kernel=kernel,
        is_inline=is_inline,
        is_streaming=is_streaming,
        template_format=template_format,
        prompt=prompt,
        arguments=KernelArguments(city="Seattle"),
    )

    request_content = logging_client.get_request_content()
    assert request_content is not None

    obtained_object = json.loads(request_content)
    assert obtained_object is not None

    data_directory = os.path.join(os.path.dirname(__file__), "data", "prompt_with_simple_variable_expected.json")
    with open(data_directory) as f:
        expected = f.read()

    expected_object = json.loads(expected)
    assert expected_object is not None

    if is_streaming:
        expected_object["stream"] = True
        expected_object["stream_options"] = {"include_usage": True}

    assert obtained_object == expected_object


# endregion

# region Test Simple Prompt


@pytest.mark.parametrize(
    "is_inline, is_streaming, template_format, prompt",
    [
        (True, False, "semantic-kernel", simple_prompt),
        (True, True, "semantic-kernel", simple_prompt),
        (False, False, "semantic-kernel", simple_prompt),
        (False, True, "semantic-kernel", simple_prompt),
        (False, False, "handlebars", simple_prompt),
        (False, True, "handlebars", simple_prompt),
        (False, False, "jinja2", simple_prompt),
        (False, True, "jinja2", simple_prompt),
    ],
)
@pytest.mark.asyncio
async def test_simple_prompt(is_inline, is_streaming, template_format, prompt):
    async_client, logging_client = get_new_client()
    ai_service = OpenAIChatCompletion(
        service_id="default",
        ai_model_id="gpt-3.5-turbo",
        async_client=async_client,
    )

    kernel = Kernel()

    kernel.add_service(ai_service)

    await run_prompt(
        kernel=kernel,
        is_inline=is_inline,
        is_streaming=is_streaming,
        template_format=template_format,
        prompt=prompt,
    )

    request_content = logging_client.get_request_content()
    assert request_content is not None

    obtained_object = json.loads(request_content)
    assert obtained_object is not None

    data_directory = os.path.join(os.path.dirname(__file__), "data", "prompt_simple_expected.json")
    with open(data_directory) as f:
        expected = f.read()

    expected_object = json.loads(expected)
    assert expected_object is not None

    if is_streaming:
        expected_object["stream"] = True
        expected_object["stream_options"] = {"include_usage": True}

    assert obtained_object == expected_object


# endregion

# region Test YAML Prompts


@pytest.mark.parametrize(
    "is_streaming, prompt_path, expected_result_path",
    [
        (False, "simple_prompt_test.yaml", "prompt_simple_expected.json"),
        (True, "simple_prompt_test.yaml", "prompt_simple_expected.json"),
        (False, "prompt_with_chat_roles_test_hb.yaml", "prompt_with_chat_roles_expected.json"),
        (True, "prompt_with_chat_roles_test_hb.yaml", "prompt_with_chat_roles_expected.json"),
        (False, "prompt_with_chat_roles_test_j2.yaml", "prompt_with_chat_roles_expected.json"),
        (True, "prompt_with_chat_roles_test_j2.yaml", "prompt_with_chat_roles_expected.json"),
        (False, "prompt_with_simple_variable_test.yaml", "prompt_with_simple_variable_expected.json"),
        (True, "prompt_with_simple_variable_test.yaml", "prompt_with_simple_variable_expected.json"),
    ],
)
@pytest.mark.asyncio
async def test_yaml_prompt(is_streaming, prompt_path, expected_result_path, kernel: Kernel):
    async_client, logging_client = get_new_client()
    ai_service = OpenAIChatCompletion(
        service_id="default",
        ai_model_id="gpt-3.5-turbo",
        async_client=async_client,
    )

    kernel.add_service(ai_service)

    prompt_dir = os.path.join(os.path.dirname(__file__), "data", f"{prompt_path}")
    with open(prompt_dir) as f:
        prompt_str = f.read()
    function = KernelFunctionFromPrompt.from_yaml(yaml_str=prompt_str, plugin_name="yaml_plugin")

    await run_function(kernel=kernel, is_streaming=is_streaming, function=function)

    request_content = logging_client.get_request_content()
    assert request_content is not None

    obtained_object = json.loads(request_content)
    assert obtained_object is not None

    data_directory = os.path.join(os.path.dirname(__file__), "data", f"{expected_result_path}")
    with open(data_directory) as f:
        expected = f.read()

    expected_object = json.loads(expected)
    assert expected_object is not None

    if is_streaming:
        expected_object["stream"] = True
        expected_object["stream_options"] = {"include_usage": True}

    assert obtained_object == expected_object


# endregion

# region Test OpenAPI Plugin Load


async def setup_openapi_function_call(kernel, function_name, arguments):
    openapi_spec_file = os.path.join(os.path.dirname(os.path.realpath(__file__)), "data", "light_bulb_api.json")

    request_details = None

    async def mock_request(request: httpx.Request):
        nonlocal request_details

        if request.method in ["POST", "PUT"]:
            request_body = None
            if request.content:
                request_body = request.content.decode()
            elif request.stream:
                try:
                    stream_content = await request.stream.read()
                    if stream_content:
                        request_body = stream_content.decode()
                except Exception:
                    request_body = None

            request_details = {
                "method": request.method,
                "url": str(request.url),
                "body": request_body,
                "headers": dict(request.headers),
            }
        else:
            request_details = {"method": request.method, "url": str(request.url), "params": dict(request.url.params)}

    transport = httpx.MockTransport(mock_request)

    async with httpx.AsyncClient(transport=transport) as client:
        plugin = kernel.add_plugin_from_openapi(
            plugin_name="LightControl",
            openapi_document_path=openapi_spec_file,
            execution_settings=OpenAPIFunctionExecutionParameters(
                http_client=client,
            ),
        )

        assert plugin is not None
        with contextlib.suppress(Exception):
            # It is expected that the API call will fail, ignore
            await run_function(kernel=kernel, is_streaming=False, function=plugin[function_name], arguments=arguments)

        return request_details


@pytest.mark.asyncio
async def test_openapi_get_lights(kernel: Kernel):
    request_content = await setup_openapi_function_call(
        kernel, function_name="GetLights", arguments=KernelArguments(roomId=1)
    )

    assert request_content is not None

    assert request_content.get("method") == "GET"
    assert request_content.get("url") == "https://127.0.0.1/Lights?roomId=1"
    assert request_content.get("params") == {"roomId": "1"}


@pytest.mark.asyncio
async def test_openapi_get_light_by_id(kernel: Kernel):
    request_content = await setup_openapi_function_call(
        kernel, function_name="GetLightById", arguments=KernelArguments(id=1)
    )

    assert request_content is not None

    assert request_content.get("method") == "GET"
    assert request_content.get("url") == "https://127.0.0.1/Lights/1"


@pytest.mark.asyncio
async def test_openapi_delete_light_by_id(kernel: Kernel):
    request_content = await setup_openapi_function_call(
        kernel, function_name="DeleteLightById", arguments=KernelArguments(id=1)
    )

    assert request_content is not None

    assert request_content.get("method") == "DELETE"
    assert request_content.get("url") == "https://127.0.0.1/Lights/1"


@pytest.mark.asyncio
async def test_openapi_create_lights(kernel: Kernel):
    request_content = await setup_openapi_function_call(
        kernel, function_name="CreateLights", arguments=KernelArguments(roomId=1, lightName="disco")
    )

    assert request_content is not None

    assert request_content.get("method") == "POST"
    assert request_content.get("url") == "https://127.0.0.1/Lights?roomId=1&lightName=disco"


@pytest.mark.asyncio
async def test_openapi_put_light_by_id(kernel: Kernel):
    request_content = await setup_openapi_function_call(
        kernel, function_name="PutLightById", arguments=KernelArguments(id=1, hexColor="11EE11")
    )

    assert request_content is not None

    assert request_content.get("method") == "PUT"
    assert request_content.get("url") == "https://127.0.0.1/Lights/1"
    assert request_content.get("body") == '{"hexColor": "11EE11"}'


# endregion
