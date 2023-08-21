# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import List

import pandas as pd
import pytest

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.open_ai.services.azure_chat_completion import (
    AzureChatCompletion,
)
from semantic_kernel.core_skills.data_skill import DataSkill


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


@pytest.fixture
def dataframe() -> pd.DataFrame:
    data = {"Name": ["Example"]}
    df = pd.DataFrame(data)
    yield df


@pytest.mark.asyncio
async def test_it_can_be_instantiated(chat_service):
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
    assert isinstance(skill.data, List)


def test_get_df_data(chat_service, dataframe):
    skill = DataSkill(chat_service)
    skill.add_data(dataframe)
    prompt = skill.get_df_data()
    assert isinstance(prompt, str)

async def test_query_async(chat_service):
    skill = DataSkill(chat_service)
    data2 = {
        "Name": ["Example"]
    }
    df = pd.DataFrame(data2)
    skill.add_data(df)
    



