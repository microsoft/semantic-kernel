# Copyright (c) Microsoft. All rights reserved.

from __future__ import annotations

import asyncio
from datetime import datetime, timezone
import httpx
import logging

from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, OpenAIChatCompletion
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIChatPromptExecutionSettings,
)
from semantic_kernel.kernel import Kernel
from semantic_kernel.utils.settings import azure_openai_settings_from_dot_env, openai_settings_from_dot_env
from openai import AsyncOpenAI, AsyncAzureOpenAI
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function_decorator import kernel_function

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


####################################################################################################
# Test 6:

# 6) Prompt with helper functions
# [!NOTE] Today, the delimiter for helper functions is a . for the out-of-the-box Semantic Kernel template engine. Out-of-the-box, we should also support the - delimiter for helper functions to align with Handlebars and the OpenAI API. The same should also be true for Jinja and future template engines.

# A prompt with helper functions. For example:

# kernel.Plugins.AddFromFunctions("Time",
#     [KernelFunctionFactory.CreateFromMethod(() => $"{DateTime.UtcNow:r}", "Now", "Gets the current date and time")]
# );

# var result = await kernel.InvokePromptAsync<ChatMessageContent>(
#     "<message role=\"system\">The current time is {{Time-Now}}</message><message role=\"user\">Can you help me tell the time in {{$city}} right now?</message>",
#     arguments: new()
#     {
#         city = "Seattle"
#     }
# );
# Rendered "intermediate" prompt:

# <message role="system">The current time is 3:00 PM</message>
# <message role="user">Can you help me tell the time in Seattle right now?</message>
####################################################################################################


class LoggingTransport(httpx.AsyncBaseTransport):
    def __init__(self, inner: httpx.AsyncBaseTransport):
        self.inner = inner

    async def handle_async_request(self, request: httpx.Request) -> httpx.Response:
        logger.info(f"Request: {request.method} {request.url}")
        if request.content:
            logger.info(f"Request Body: {request.content.decode('utf-8')}")
        elif request.stream:
            stream_content = await request.stream.aread()
            logger.info(f"Request Stream Content: {stream_content.decode('utf-8')}")
            request.stream = httpx.AsyncByteStream(stream_content)

        response = await self.inner.handle_async_request(request)
        return response


class LoggingAsyncClient(httpx.AsyncClient):
    def __init__(self, *args, **kwargs):
        transport = kwargs.pop('transport', None)
        super().__init__(*args, **kwargs, transport=LoggingTransport(transport or httpx.AsyncHTTPTransport()))

class City:
    def __init__(self, name: str):
        self.name = name

class Time:
    @kernel_function(name="Now")
    def time_now() -> str:
        return f"{datetime.now(timezone.utc):%I:%M %p}"

async def main():
    kernel = Kernel()

    use_azure_openai = False
    service_id = "test-6"
    if use_azure_openai:

        deployment_name, api_key, endpoint, api_version = azure_openai_settings_from_dot_env(include_api_version=True)
        logging_async_client = LoggingAsyncClient()
        async_client = AsyncAzureOpenAI(
            api_key=api_key,
            azure_endpoint=endpoint,
            azure_deployment=deployment_name,
            http_client=logging_async_client,
            api_version=api_version,
        )

        ai_service = AzureChatCompletion(
            service_id=service_id,
            deployment_name=deployment_name,
            async_client=async_client,
        )
    else:
        api_key, _ = openai_settings_from_dot_env()
        logging_async_client = LoggingAsyncClient()
        async_client = AsyncOpenAI(api_key=api_key, http_client=logging_async_client)
        ai_service = OpenAIChatCompletion(
            service_id=service_id,
            ai_model_id="gpt-3.5-turbo-1106",
            async_client=async_client,
        )
    kernel.add_service(ai_service)

    settings: OpenAIChatPromptExecutionSettings = kernel.get_prompt_execution_settings_from_service_id(
        service_id=service_id
    )

    kernel.add_plugin(plugin=Time(), plugin_name="Time")

    print(
        await kernel.invoke_prompt(
            function_name="prompt_test_6",
            plugin_name="test_6",
            prompt="<message role=\"system\">The current time is {{Time.Now}}</message><message role=\"user\">Can you help me tell the time in {{$city}} right now?</message>",
            settings=settings,
            arguments=KernelArguments(city="Seattle"),
        )
    )

    await logging_async_client.aclose()

if __name__ == "__main__":
    asyncio.run(main())
