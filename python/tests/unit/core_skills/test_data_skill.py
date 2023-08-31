# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import List
from unittest.mock import AsyncMock, patch

import pandas as pd
import pytest

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.chat_request_settings import ChatRequestSettings
from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import (
    AzureChatCompletion,
)
from semantic_kernel.core_skills.data_skill import DataSkill

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


@pytest.fixture
def dataframe() -> pd.DataFrame:
    data = {"Name": ["Example"]}
    df = pd.DataFrame(data)
    yield df


def test_it_can_be_instantiated(chat_service):
    skill = DataSkill(chat_service)
    assert skill is not None


def test_it_can_be_imported(chat_service):
    kernel = Kernel()
    skill = DataSkill(chat_service)
    assert kernel.import_skill(skill, "data")
    assert kernel.skills.has_native_function("data", "queryAsync")


def test_add_data_and_clear_data(chat_service, dataframe):
    skill = DataSkill(chat_service)
    data_param = "text.csv"
    try:
        skill.add_data(data_param)
    except FileNotFoundError:
        pass
    skill.add_data(dataframe)
    assert isinstance(skill.data, List)
    skill.clear_data()
    assert len(skill.data) == 0


def test_get_df_data(chat_service, dataframe):
    skill = DataSkill(chat_service)
    skill.add_data(dataframe)
    prompt = skill.get_df_data()
    assert isinstance(prompt, str) and len(prompt)


@pytest.mark.asyncio
async def test_query_async(chat_service, chat_req_settings, dataframe):
    mock_openai = AsyncMock()
    with patch(
        "semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion.openai",
        new=mock_openai,
    ):
        user_prompt = "hello world"
        code_prompt = (
            "You are working with 1 Pandas dataframe(s) in Python, named df1, df2, and so on.\n"
            "The header of df1 is:\n"
            '[{"Name":"Example"}]\n\n'
            "The preceding is a summary of the data. There may be more rows. "
            "Write a Python function `process(df1)` where df1 is/are Pandas dataframe(s). "
            f"This is the function's purpose: {user_prompt} "
            "Write the function in a Python code block with all necessary imports. "
            "Do not include any example usage. Do not include any explanation nor decoration. "
            "Store the reult in a local variable named `result`."
        )
        expected_messages = [{"role": "user", "content": code_prompt}]

        data_skill = DataSkill(chat_service, sources=dataframe)

        # Test endpoint does not generate response, pass through
        try:
            await data_skill.query_async(user_prompt)
        except AssertionError:
            pass

        mock_openai.ChatCompletion.acreate.assert_called_with(
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
async def test_transform_async(chat_service, chat_req_settings, dataframe):
    mock_openai = AsyncMock()
    with patch(
        "semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion.openai",
        new=mock_openai,
    ):
        prompt = "hello world"
        code_prompt = (
            "You are working with 1 Pandas dataframe(s) in Python, named df1, df2, and so on.\n"
            "The header of df1 is:\n"
            '[{"Name":"Example"}]\n\n'
            "The preceding is a summary of the data. There may be more rows. "
            "Write Python code to transform the data as the user asked. "
            "If the user wants to transform more than one dataframe, return a list of the transformed "
            "dataframes. Otherwise, return a single transformed dataframe. "
            "Write a Python function `process(df1)` where df1 is/are Pandas dataframe(s). "
            f"This is the function's purpose: {prompt} "
            "Write the function in a Python code block with all necessary imports. "
            "Do not include any example usage. Do not include any explanation nor decoration. "
            "Store the reult in a local variable named `result`."
        )
        expected_messages = [{"role": "user", "content": code_prompt}]

        data_skill = DataSkill(chat_service, sources=dataframe)

        # Test endpoint does not generate response, pass through
        try:
            await data_skill.transform_async(prompt)
        except AssertionError:
            pass

        mock_openai.ChatCompletion.acreate.assert_called_with(
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
