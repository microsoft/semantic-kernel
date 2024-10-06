# Copyright (c) Microsoft. All rights reserved.


import json
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from openai import AsyncStream
from openai.resources import AsyncCompletions
from openai.types import Completion as TextCompletion
from openai.types import CompletionChoice as TextCompletionChoice

from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAITextPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.open_ai.services.open_ai_text_completion import (
    OpenAITextCompletion,
)
from semantic_kernel.connectors.ai.prompt_execution_settings import (
    PromptExecutionSettings,
)
from semantic_kernel.connectors.ai.text_completion_client_base import (
    TextCompletionClientBase,
)
from semantic_kernel.exceptions.service_exceptions import ServiceInitializationError


def test_init(openai_unit_test_env) -> None:
    # Test successful initialization
    open_ai_text_completion = OpenAITextCompletion()

    assert (
        open_ai_text_completion.ai_model_id
        == openai_unit_test_env["OPENAI_TEXT_MODEL_ID"]
    )
    assert isinstance(open_ai_text_completion, TextCompletionClientBase)


def test_init_with_ai_model_id(openai_unit_test_env) -> None:
    # Test successful initialization
    ai_model_id = "test_model_id"
    open_ai_text_completion = OpenAITextCompletion(ai_model_id=ai_model_id)

    assert open_ai_text_completion.ai_model_id == ai_model_id
    assert isinstance(open_ai_text_completion, TextCompletionClientBase)


def test_init_with_default_header(openai_unit_test_env) -> None:
    default_headers = {"X-Unit-Test": "test-guid"}

    # Test successful initialization
    open_ai_text_completion = OpenAITextCompletion(
        default_headers=default_headers,
    )

    assert (
        open_ai_text_completion.ai_model_id
        == openai_unit_test_env["OPENAI_TEXT_MODEL_ID"]
    )
    assert isinstance(open_ai_text_completion, TextCompletionClientBase)
    for key, value in default_headers.items():
        assert key in open_ai_text_completion.client.default_headers
        assert open_ai_text_completion.client.default_headers[key] == value


def test_init_validation_fail() -> None:
    with pytest.raises(ServiceInitializationError):
        OpenAITextCompletion(api_key="34523", ai_model_id={"test": "dict"})


@pytest.mark.parametrize("exclude_list", [["OPENAI_API_KEY"]], indirect=True)
def test_init_with_empty_api_key(openai_unit_test_env) -> None:
    with pytest.raises(ServiceInitializationError):
        OpenAITextCompletion(
            env_file_path="test.env",
        )


@pytest.mark.parametrize("exclude_list", [["OPENAI_TEXT_MODEL_ID"]], indirect=True)
def test_init_with_empty_model(openai_unit_test_env) -> None:
    with pytest.raises(ServiceInitializationError):
        OpenAITextCompletion(
            env_file_path="test.env",
        )


def test_serialize(openai_unit_test_env) -> None:
    default_headers = {"X-Unit-Test": "test-guid"}

    settings = {
        "ai_model_id": openai_unit_test_env["OPENAI_TEXT_MODEL_ID"],
        "api_key": openai_unit_test_env["OPENAI_API_KEY"],
        "default_headers": default_headers,
    }

    open_ai_text_completion = OpenAITextCompletion.from_dict(settings)
    dumped_settings = open_ai_text_completion.to_dict()
    assert (
        dumped_settings["ai_model_id"] == openai_unit_test_env["OPENAI_TEXT_MODEL_ID"]
    )
    assert dumped_settings["api_key"] == openai_unit_test_env["OPENAI_API_KEY"]
    # Assert that the default header we added is present in the dumped_settings default headers
    for key, value in default_headers.items():
        assert key in dumped_settings["default_headers"]
        assert dumped_settings["default_headers"][key] == value


def test_serialize_def_headers_string(openai_unit_test_env) -> None:
    default_headers = '{"X-Unit-Test": "test-guid"}'

    settings = {
        "ai_model_id": openai_unit_test_env["OPENAI_TEXT_MODEL_ID"],
        "api_key": openai_unit_test_env["OPENAI_API_KEY"],
        "default_headers": default_headers,
    }

    open_ai_text_completion = OpenAITextCompletion.from_dict(settings)
    dumped_settings = open_ai_text_completion.to_dict()
    assert (
        dumped_settings["ai_model_id"] == openai_unit_test_env["OPENAI_TEXT_MODEL_ID"]
    )
    assert dumped_settings["api_key"] == openai_unit_test_env["OPENAI_API_KEY"]
    # Assert that the default header we added is present in the dumped_settings default headers
    for key, value in json.loads(default_headers).items():
        assert key in dumped_settings["default_headers"]
        assert dumped_settings["default_headers"][key] == value


def test_serialize_with_org_id(openai_unit_test_env) -> None:
    settings = {
        "ai_model_id": openai_unit_test_env["OPENAI_TEXT_MODEL_ID"],
        "api_key": openai_unit_test_env["OPENAI_API_KEY"],
        "org_id": openai_unit_test_env["OPENAI_ORG_ID"],
    }

    open_ai_text_completion = OpenAITextCompletion.from_dict(settings)
    dumped_settings = open_ai_text_completion.to_dict()
    assert (
        dumped_settings["ai_model_id"] == openai_unit_test_env["OPENAI_TEXT_MODEL_ID"]
    )
    assert dumped_settings["api_key"] == openai_unit_test_env["OPENAI_API_KEY"]
    assert dumped_settings["org_id"] == openai_unit_test_env["OPENAI_ORG_ID"]


# region Get Text Contents


@pytest.fixture()
def completion_response() -> TextCompletion:
    return TextCompletion(
        id="test",
        choices=[TextCompletionChoice(text="test", index=0, finish_reason="stop")],
        created=0,
        model="test",
        object="text_completion",
    )


@pytest.fixture()
def streaming_completion_response() -> AsyncStream[TextCompletion]:
    content = TextCompletion(
        id="test",
        choices=[TextCompletionChoice(text="test", index=0, finish_reason="stop")],
        created=0,
        model="test",
        object="text_completion",
    )
    stream = MagicMock(spec=AsyncStream)
    stream.__aiter__.return_value = [content]
    return stream


@pytest.mark.asyncio
@patch.object(AsyncCompletions, "create", new_callable=AsyncMock)
async def test_tc(
    mock_create,
    openai_unit_test_env,
    completion_response,
) -> None:
    mock_create.return_value = completion_response
    complete_prompt_execution_settings = OpenAITextPromptExecutionSettings(
        service_id="test_service_id"
    )

    openai_text_completion = OpenAITextCompletion()
    await openai_text_completion.get_text_contents(
        prompt="test", settings=complete_prompt_execution_settings
    )
    mock_create.assert_awaited_once_with(
        model=openai_unit_test_env["OPENAI_TEXT_MODEL_ID"],
        stream=False,
        prompt="test",
        echo=False,
    )


@pytest.mark.asyncio
@patch.object(AsyncCompletions, "create", new_callable=AsyncMock)
async def test_tc_singular(
    mock_create,
    openai_unit_test_env,
    completion_response,
) -> None:
    mock_create.return_value = completion_response
    complete_prompt_execution_settings = OpenAITextPromptExecutionSettings(
        service_id="test_service_id"
    )

    openai_text_completion = OpenAITextCompletion()
    await openai_text_completion.get_text_content(
        prompt="test", settings=complete_prompt_execution_settings
    )
    mock_create.assert_awaited_once_with(
        model=openai_unit_test_env["OPENAI_TEXT_MODEL_ID"],
        stream=False,
        prompt="test",
        echo=False,
    )


@pytest.mark.asyncio
@patch.object(AsyncCompletions, "create", new_callable=AsyncMock)
async def test_tc_prompt_execution_settings(
    mock_create,
    openai_unit_test_env,
    completion_response,
) -> None:
    mock_create.return_value = completion_response
    complete_prompt_execution_settings = PromptExecutionSettings(
        service_id="test_service_id"
    )

    openai_text_completion = OpenAITextCompletion()
    await openai_text_completion.get_text_contents(
        prompt="test", settings=complete_prompt_execution_settings
    )
    mock_create.assert_awaited_once_with(
        model=openai_unit_test_env["OPENAI_TEXT_MODEL_ID"],
        stream=False,
        prompt="test",
        echo=False,
    )


# region Streaming


@pytest.mark.asyncio
@patch.object(AsyncCompletions, "create", new_callable=AsyncMock)
async def test_stc(
    mock_create,
    openai_unit_test_env,
    streaming_completion_response,
) -> None:
    mock_create.return_value = streaming_completion_response
    complete_prompt_execution_settings = OpenAITextPromptExecutionSettings(
        service_id="test_service_id"
    )

    openai_text_completion = OpenAITextCompletion()
    [
        text
        async for text in openai_text_completion.get_streaming_text_contents(
            prompt="test", settings=complete_prompt_execution_settings
        )
    ]
    mock_create.assert_awaited_once_with(
        model=openai_unit_test_env["OPENAI_TEXT_MODEL_ID"],
        stream=True,
        prompt="test",
        echo=False,
    )


@pytest.mark.asyncio
@patch.object(AsyncCompletions, "create", new_callable=AsyncMock)
async def test_stc_singular(
    mock_create,
    openai_unit_test_env,
    streaming_completion_response,
) -> None:
    mock_create.return_value = streaming_completion_response
    complete_prompt_execution_settings = OpenAITextPromptExecutionSettings(
        service_id="test_service_id"
    )

    openai_text_completion = OpenAITextCompletion()
    [
        text
        async for text in openai_text_completion.get_streaming_text_content(
            prompt="test", settings=complete_prompt_execution_settings
        )
    ]
    mock_create.assert_awaited_once_with(
        model=openai_unit_test_env["OPENAI_TEXT_MODEL_ID"],
        stream=True,
        prompt="test",
        echo=False,
    )


@pytest.mark.asyncio
@patch.object(AsyncCompletions, "create", new_callable=AsyncMock)
async def test_stc_prompt_execution_settings(
    mock_create,
    openai_unit_test_env,
    streaming_completion_response,
) -> None:
    mock_create.return_value = streaming_completion_response
    complete_prompt_execution_settings = PromptExecutionSettings(
        service_id="test_service_id"
    )

    openai_text_completion = OpenAITextCompletion()
    [
        text
        async for text in openai_text_completion.get_streaming_text_contents(
            prompt="test", settings=complete_prompt_execution_settings
        )
    ]
    mock_create.assert_awaited_once_with(
        model=openai_unit_test_env["OPENAI_TEXT_MODEL_ID"],
        stream=True,
        prompt="test",
        echo=False,
    )


@pytest.mark.asyncio
@patch.object(AsyncCompletions, "create", new_callable=AsyncMock)
async def test_stc_empty_choices(
    mock_create,
    openai_unit_test_env,
) -> None:
    content1 = TextCompletion(
        id="test",
        choices=[],
        created=0,
        model="test",
        object="text_completion",
    )
    content2 = TextCompletion(
        id="test",
        choices=[TextCompletionChoice(text="test", index=0, finish_reason="stop")],
        created=0,
        model="test",
        object="text_completion",
    )
    stream = MagicMock(spec=AsyncStream)
    stream.__aiter__.return_value = [content1, content2]
    mock_create.return_value = stream
    complete_prompt_execution_settings = OpenAITextPromptExecutionSettings(
        service_id="test_service_id"
    )

    openai_text_completion = OpenAITextCompletion()
    results = [
        text
        async for text in openai_text_completion.get_streaming_text_contents(
            prompt="test", settings=complete_prompt_execution_settings
        )
    ]
    assert len(results) == 1
    mock_create.assert_awaited_once_with(
        model=openai_unit_test_env["OPENAI_TEXT_MODEL_ID"],
        stream=True,
        prompt="test",
        echo=False,
    )
