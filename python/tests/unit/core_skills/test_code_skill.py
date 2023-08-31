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

TEST_DEPLOYMENT = "test_deployment"
TEST_ENDPOINT = "https://test-endpoint.com"
TEST_API_KEY = "test_api_key"
TEST_API_TYPE = "azure"
TEST_API_VER = "2023-03-15-preview"


@pytest.fixture
def chat_service() -> AzureChatCompletion:
    logger = Logger("test_logger")
    azure_chat_completion = AzureChatCompletion(
        deployment_name=TEST_DEPLOYMENT,
        endpoint=TEST_ENDPOINT,
        api_key=TEST_API_KEY,
        api_version=TEST_API_VER,
        logger=logger,
    )
    yield azure_chat_completion


@pytest.fixture
def chat_req_settings() -> ChatRequestSettings:
    crs = ChatRequestSettings(temperature=0.1)
    yield crs


def test_can_be_instantiated(chat_service: AzureChatCompletion):
    skill = CodeSkill(chat_service)
    assert skill is not None


def test_functions_can_be_imported(chat_service: AzureChatCompletion):
    kernel = Kernel()
    assert kernel.import_skill(CodeSkill(chat_service), "code")
    assert kernel.skills.has_native_function("code", "codeAsync")
    assert kernel.skills.has_native_function("code", "executeAsync")
    assert kernel.skills.has_native_function("code", "executeCodeAsync")


@pytest.mark.asyncio
async def test_code_call_with_parameters(
    chat_service: AzureChatCompletion, chat_req_settings: ChatRequestSettings
):
    mock_openai = AsyncMock()
    with patch(
        "semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion.openai",
        new=mock_openai,
    ):
        user_prompt = "hello world"
        expected_messages = [
            {"role": "user", "content": f"{DEFAULT_PROMPT}{user_prompt}"}
        ]

        skill = CodeSkill(chat_service)

        # Test endpoint does not generate response, pass through
        try:
            await skill.code_async(user_prompt)
        except AssertionError:
            pass

        mock_openai.ChatCompletion.acreate.assert_called_once_with(
            engine=TEST_DEPLOYMENT,
            api_key=TEST_API_KEY,
            api_type=TEST_API_TYPE,
            api_base=TEST_ENDPOINT,
            api_version=TEST_API_VER,
            organization=None,
            messages=expected_messages,
            temperature=chat_req_settings.temperature,
            max_tokens=chat_req_settings.max_tokens,
            top_p=chat_req_settings.top_p,
            presence_penalty=chat_req_settings.presence_penalty,
            frequency_penalty=chat_req_settings.frequency_penalty,
            n=chat_req_settings.number_of_responses,
            stream=False,
            stop=None,
            logit_bias={},
        )


@pytest.mark.asyncio
async def test_execute_call_with_parameters(
    chat_service: AzureChatCompletion, chat_req_settings: ChatRequestSettings
):
    mock_openai = AsyncMock()
    with patch(
        "semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion.openai",
        new=mock_openai,
    ):
        user_prompt = "hello world"
        expected_messages = [
            {"role": "user", "content": f"{DEFAULT_PROMPT}{user_prompt}"}
        ]

        skill = CodeSkill(chat_service)

        # Test endpoint does not generate response, pass through
        try:
            await skill.execute_async(user_prompt)
        except AssertionError:
            pass

        mock_openai.ChatCompletion.acreate.assert_called_once_with(
            engine=TEST_DEPLOYMENT,
            api_key=TEST_API_KEY,
            api_type=TEST_API_TYPE,
            api_base=TEST_ENDPOINT,
            api_version=TEST_API_VER,
            organization=None,
            messages=expected_messages,
            temperature=chat_req_settings.temperature,
            max_tokens=chat_req_settings.max_tokens,
            top_p=chat_req_settings.top_p,
            presence_penalty=chat_req_settings.presence_penalty,
            frequency_penalty=chat_req_settings.frequency_penalty,
            n=chat_req_settings.number_of_responses,
            stream=False,
            stop=None,
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
    assert test_local_vars.get("r")
    assert test_local_vars.get("assign") == 3
    assert test_local_vars.get("counter") == 3
