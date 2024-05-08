# Copyright (c) Microsoft. All rights reserved.

from __future__ import annotations

import asyncio
import httpx
import logging

from semantic_kernel.connectors.ai.open_ai import AzureChatCompletion, OpenAIChatCompletion
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIChatPromptExecutionSettings,
)
from semantic_kernel.kernel import Kernel
from semantic_kernel.utils.settings import azure_openai_settings_from_dot_env, openai_settings_from_dot_env
from openai import AsyncOpenAI, AsyncAzureOpenAI

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.DEBUG)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)


####################################################################################################
# Test 1:

# 1) Simple prompt
# A prompt with a single user message. For example:

# var result = await kernel.InvokePromptAsync<ChatMessageContent>(
#     "Can you help me tell the time in Seattle right now?"
# );
# Rendered "intermediate" prompt:

# <message role="user">Can you help me tell the time in Seattle right now?</message>
# This will validate that each language can take a string input and generate the same request body.
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


async def main():
    kernel = Kernel()

    use_azure_openai = True
    service_id = "test-1"
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

    print(
        await kernel.invoke_prompt(
            function_name="prompt_test_1",
            plugin_name="test_1",
            prompt="Can you help me tell the time in Seattle right now?",
            settings=settings,
        )
    )

    await logging_async_client.aclose()

if __name__ == "__main__":
    asyncio.run(main())
