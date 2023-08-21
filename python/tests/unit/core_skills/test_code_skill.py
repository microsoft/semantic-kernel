# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from unittest.mock import AsyncMock, patch

import pytest

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.chat_request_settings import ChatRequestSettings
from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import (
    AzureChatCompletion,
)
from semantic_kernel.core_skills.code_skill import DEFAULT_PROMPT, ON_SUCCESS, CodeSkill


@pytest.fixture
def chat_service() -> AzureChatCompletion:
    deployment_name = "test_deployment"
    endpoint = "https://test-endpoint.com"
    api_key = "test_api_key"
    api_version = "2023-03-15-preview"
    logger = Logger("test_logger")
    azure_chat_completion = AzureChatCompletion(
        deployment_name=deployment_name,
        endpoint=endpoint,
        api_key=api_key,
        api_version=api_version,
        logger=logger,
    )
    yield azure_chat_completion


def test_can_be_instantiated(chat_service: AzureChatCompletion):
    skill = CodeSkill(chat_service)
    assert skill is not None


def test_functions_can_be_imported():
    kernel = Kernel()
    assert kernel.import_skill(CodeSkill(chat_service), "code")
    assert kernel.skills.has_native_function("code", "codeAsync")
    assert kernel.skills.has_native_function("code", "executeAsync")
    assert kernel.skills.has_native_function("code", "executeCodeAsync")


@pytest.mark.asyncio
async def test_code_call_with_parameters(chat_service: AzureChatCompletion):
    mock_openai = AsyncMock()
    with patch(
        "semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion.openai",
        new=mock_openai,
    ):
        deployment_name = "test_deployment"
        prompt = "hello world"
        messages = [{"role": "user", "content": f"{DEFAULT_PROMPT}{prompt}"}]
        chat_request_settings = ChatRequestSettings(temperature=0.1)

        azure_chat_completion = chat_service

        skill = CodeSkill(service=azure_chat_completion)

        # Will not generate anything from test
        try:
            await skill.code_async(prompt)
        except AssertionError:
            pass

        mock_openai.ChatCompletion.acreate.assert_called_once_with(
            engine=deployment_name,
            api_key=azure_chat_completion._api_key,
            api_type=azure_chat_completion._api_type,
            api_base=azure_chat_completion._endpoint,
            api_version=azure_chat_completion._api_version,
            organization=None,
            messages=messages,
            temperature=chat_request_settings.temperature,
            max_tokens=chat_request_settings.max_tokens,
            top_p=chat_request_settings.top_p,
            presence_penalty=chat_request_settings.presence_penalty,
            frequency_penalty=chat_request_settings.frequency_penalty,
            n=chat_request_settings.number_of_responses,
            stream=False,
            logit_bias={},
        )


@pytest.mark.asyncio
async def test_execute_call_with_parameters(chat_service: AzureChatCompletion):
    mock_openai = AsyncMock()
    with patch(
        "semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion.openai",
        new=mock_openai,
    ):
        deployment_name = "test_deployment"
        prompt = "hello world"
        messages = [{"role": "user", "content": f"{DEFAULT_PROMPT}{prompt}"}]
        chat_request_settings = ChatRequestSettings(temperature=0.1)

        azure_chat_completion = chat_service

        skill = CodeSkill(service=azure_chat_completion)

        # No code generated from test endpoint, move on
        try:
            await skill.execute_async(prompt)
        except AssertionError:
            pass

        mock_openai.ChatCompletion.acreate.assert_called_once_with(
            engine=deployment_name,
            api_key=azure_chat_completion._api_key,
            api_type=azure_chat_completion._api_type,
            api_base=azure_chat_completion._endpoint,
            api_version=azure_chat_completion._api_version,
            organization=None,
            messages=messages,
            temperature=chat_request_settings.temperature,
            max_tokens=chat_request_settings.max_tokens,
            top_p=chat_request_settings.top_p,
            presence_penalty=chat_request_settings.presence_penalty,
            frequency_penalty=chat_request_settings.frequency_penalty,
            n=chat_request_settings.number_of_responses,
            stream=False,
            logit_bias={},
        )


@pytest.mark.asyncio
async def test_execute_code():
    # No chat completion calls done
    skill = CodeSkill(None)
    code = """test = 2"""
    assert await skill.execute_code_async(code) == ON_SUCCESS


@pytest.mark.asyncio
async def test_custom_execute():
    # No chat completion calls done
    skill = CodeSkill(None)
    # Test built-in import, assignment, iteration
    code = "import random as r\nassign = 3\ncounter = 0\nfor i in range(3):\n\tcounter += 1"
    test_global_vars = {}
    test_local_vars = {}

    assert (
        await skill.custom_execute_async(code, test_global_vars, test_local_vars)
        == ON_SUCCESS
    )
    print(test_local_vars)
    assert test_local_vars.get("r")
    assert test_local_vars.get("assign") == 3
    assert test_local_vars.get("counter") == 3
