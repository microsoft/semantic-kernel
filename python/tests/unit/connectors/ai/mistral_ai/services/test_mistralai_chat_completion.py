# Copyright (c) Microsoft. All rights reserved.
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mistralai.async_client import MistralAsyncClient

from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.connectors.ai.mistral_ai.prompt_execution_settings.mistral_ai_prompt_execution_settings import (
    MistralAIChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.mistral_ai.services.mistral_ai_chat_completion import MistralAIChatCompletion
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIChatPromptExecutionSettings,
)
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import (
    ChatMessageContent,
    FunctionCallContent,
    TextContent,
)
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions import (
    ServiceInitializationError,
    ServiceInvalidExecutionSettingsError,
    ServiceResponseException,
)
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.kernel import Kernel


@pytest.fixture
def mock_settings() -> MistralAIChatPromptExecutionSettings:
    return MistralAIChatPromptExecutionSettings()


@pytest.fixture
def mock_mistral_ai_client_completion() -> MistralAsyncClient:
    client = MagicMock(spec=MistralAsyncClient)
    chat_completion_response = AsyncMock()
    choices = [MagicMock(finish_reason="stop", message=MagicMock(role="assistant", content="Test"))]
    chat_completion_response.choices = choices
    client.chat.return_value = chat_completion_response
    return client


@pytest.fixture
def mock_mistral_ai_client_completion_stream() -> MistralAsyncClient:
    client = MagicMock(spec=MistralAsyncClient)
    chat_completion_response = MagicMock()
    choices = [
        MagicMock(finish_reason="stop", delta=MagicMock(role="assistant", content="Test")),
        MagicMock(finish_reason="stop", delta=MagicMock(role="assistant", content="Test", tool_calls=None)),
    ]
    chat_completion_response.choices = choices
    chat_completion_response_empty = MagicMock()
    chat_completion_response_empty.choices = []
    generator_mock = MagicMock()
    generator_mock.__aiter__.return_value = [chat_completion_response_empty, chat_completion_response]
    client.chat_stream.return_value = generator_mock
    return client


@pytest.mark.asyncio
async def test_complete_chat_contents(
    kernel: Kernel,
    mock_settings: MistralAIChatPromptExecutionSettings,
    mock_mistral_ai_client_completion: MistralAsyncClient,
):
    chat_history = MagicMock()
    arguments = KernelArguments()
    chat_completion_base = MistralAIChatCompletion(
        ai_model_id="test_model_id", service_id="test", api_key="", async_client=mock_mistral_ai_client_completion
    )

    content: list[ChatMessageContent] = await chat_completion_base.get_chat_message_contents(
        chat_history=chat_history, settings=mock_settings, kernel=kernel, arguments=arguments
    )
    assert content is not None


mock_message_text_content = ChatMessageContent(role=AuthorRole.ASSISTANT, items=[TextContent(text="test")])

mock_message_function_call = ChatMessageContent(
    role=AuthorRole.ASSISTANT,
    items=[
        FunctionCallContent(
            name="test",
            arguments={"key": "test"},
        )
    ],
)


@pytest.mark.parametrize(
    "function_choice_behavior,model_responses,expected_result",
    [
        pytest.param(
            FunctionChoiceBehavior.Auto(),
            [[mock_message_function_call], [mock_message_text_content]],
            TextContent,
            id="auto",
        ),
        pytest.param(
            FunctionChoiceBehavior.Auto(auto_invoke=False),
            [[mock_message_function_call]],
            FunctionCallContent,
            id="auto_none_invoke",
        ),
        pytest.param(
            FunctionChoiceBehavior.Required(auto_invoke=False),
            [[mock_message_function_call]],
            FunctionCallContent,
            id="required_none_invoke",
        ),
        pytest.param(FunctionChoiceBehavior.NoneInvoke(), [[mock_message_text_content]], TextContent, id="none"),
    ],
)
@pytest.mark.asyncio
async def test_complete_chat_contents_function_call_behavior_tool_call(
    kernel: Kernel,
    mock_settings: MistralAIChatPromptExecutionSettings,
    function_choice_behavior: FunctionChoiceBehavior,
    model_responses,
    expected_result,
):
    kernel.add_function("test", kernel_function(lambda key: "test", name="test"))
    mock_settings.function_choice_behavior = function_choice_behavior

    arguments = KernelArguments()
    chat_completion_base = MistralAIChatCompletion(ai_model_id="test_model_id", service_id="test", api_key="")

    with (
        patch.object(chat_completion_base, "_inner_get_chat_message_contents", side_effect=model_responses),
    ):
        response: list[ChatMessageContent] = await chat_completion_base.get_chat_message_contents(
            chat_history=ChatHistory(system_message="Test"), settings=mock_settings, kernel=kernel, arguments=arguments
        )

        assert all(isinstance(content, expected_result) for content in response[0].items)


@pytest.mark.asyncio
async def test_complete_chat_contents_function_call_behavior_without_kernel(
    mock_settings: MistralAIChatPromptExecutionSettings,
    mock_mistral_ai_client_completion: MistralAsyncClient,
):
    chat_history = MagicMock()
    chat_completion_base = MistralAIChatCompletion(
        ai_model_id="test_model_id", service_id="test", api_key="", async_client=mock_mistral_ai_client_completion
    )

    mock_settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

    with pytest.raises(ServiceInvalidExecutionSettingsError):
        await chat_completion_base.get_chat_message_contents(chat_history=chat_history, settings=mock_settings)


@pytest.mark.asyncio
async def test_complete_chat_stream_contents(
    kernel: Kernel,
    mock_settings: MistralAIChatPromptExecutionSettings,
    mock_mistral_ai_client_completion_stream: MistralAsyncClient,
):
    chat_history = MagicMock()
    arguments = KernelArguments()

    chat_completion_base = MistralAIChatCompletion(
        ai_model_id="test_model_id",
        service_id="test",
        api_key="",
        async_client=mock_mistral_ai_client_completion_stream,
    )

    async for content in chat_completion_base.get_streaming_chat_message_contents(
        chat_history, mock_settings, kernel=kernel, arguments=arguments
    ):
        assert content is not None


mock_message_function_call = StreamingChatMessageContent(
    role=AuthorRole.ASSISTANT, items=[FunctionCallContent(name="test")], choice_index="0"
)

mock_message_text_content = StreamingChatMessageContent(
    role=AuthorRole.ASSISTANT, items=[TextContent(text="test")], choice_index="0"
)


@pytest.mark.parametrize(
    "function_choice_behavior,model_responses,expected_result",
    [
        pytest.param(
            FunctionChoiceBehavior.Auto(),
            [[mock_message_function_call], [mock_message_text_content]],
            TextContent,
            id="auto",
        ),
        pytest.param(
            FunctionChoiceBehavior.Auto(auto_invoke=False),
            [[mock_message_function_call]],
            FunctionCallContent,
            id="auto_none_invoke",
        ),
        pytest.param(
            FunctionChoiceBehavior.Required(auto_invoke=False),
            [[mock_message_function_call]],
            FunctionCallContent,
            id="required_none_invoke",
        ),
        pytest.param(FunctionChoiceBehavior.NoneInvoke(), [[mock_message_text_content]], TextContent, id="none"),
    ],
)
@pytest.mark.asyncio
async def test_complete_chat_contents_streaming_function_call_behavior_tool_call(
    kernel: Kernel,
    mock_settings: MistralAIChatPromptExecutionSettings,
    function_choice_behavior: FunctionChoiceBehavior,
    model_responses,
    expected_result,
):
    mock_settings.function_choice_behavior = function_choice_behavior

    # Mock sequence of model responses
    generator_mocks = []
    for mock_message in model_responses:
        generator_mock = MagicMock()
        generator_mock.__aiter__.return_value = [mock_message]
        generator_mocks.append(generator_mock)

    arguments = KernelArguments()
    chat_completion_base = MistralAIChatCompletion(ai_model_id="test_model_id", service_id="test", api_key="")

    with patch.object(chat_completion_base, "_inner_get_streaming_chat_message_contents", side_effect=generator_mocks):
        messages = []
        async for chunk in chat_completion_base.get_streaming_chat_message_contents(
            chat_history=ChatHistory(system_message="Test"), settings=mock_settings, kernel=kernel, arguments=arguments
        ):
            messages.append(chunk)

        response = messages[-1]
        assert all(isinstance(content, expected_result) for content in response[0].items)


@pytest.mark.asyncio
async def test_mistral_ai_sdk_exception(kernel: Kernel, mock_settings: MistralAIChatPromptExecutionSettings):
    chat_history = MagicMock()
    arguments = KernelArguments()
    client = MagicMock(spec=MistralAsyncClient)
    client.chat.side_effect = Exception("Test Exception")

    chat_completion_base = MistralAIChatCompletion(
        ai_model_id="test_model_id", service_id="test", api_key="", async_client=client
    )

    with pytest.raises(ServiceResponseException):
        await chat_completion_base.get_chat_message_contents(
            chat_history=chat_history, settings=mock_settings, kernel=kernel, arguments=arguments
        )


@pytest.mark.asyncio
async def test_mistral_ai_sdk_exception_streaming(kernel: Kernel, mock_settings: MistralAIChatPromptExecutionSettings):
    chat_history = MagicMock()
    arguments = KernelArguments()
    client = MagicMock(spec=MistralAsyncClient)
    client.chat_stream.side_effect = Exception("Test Exception")

    chat_completion_base = MistralAIChatCompletion(
        ai_model_id="test_model_id", service_id="test", api_key="", async_client=client
    )

    with pytest.raises(ServiceResponseException):
        async for content in chat_completion_base.get_streaming_chat_message_contents(
            chat_history, mock_settings, kernel=kernel, arguments=arguments
        ):
            assert content is not None


def test_mistral_ai_chat_completion_init(mistralai_unit_test_env) -> None:
    # Test successful initialization
    mistral_ai_chat_completion = MistralAIChatCompletion()

    assert mistral_ai_chat_completion.ai_model_id == mistralai_unit_test_env["MISTRALAI_CHAT_MODEL_ID"]
    assert mistral_ai_chat_completion.async_client._api_key == mistralai_unit_test_env["MISTRALAI_API_KEY"]
    assert isinstance(mistral_ai_chat_completion, ChatCompletionClientBase)


@pytest.mark.parametrize("exclude_list", [["MISTRALAI_API_KEY", "MISTRALAI_CHAT_MODEL_ID"]], indirect=True)
def test_mistral_ai_chat_completion_init_constructor(mistralai_unit_test_env) -> None:
    # Test successful initialization
    mistral_ai_chat_completion = MistralAIChatCompletion(
        api_key="overwrite_api_key",
        ai_model_id="overwrite_model_id",
        env_file_path="test.env",
    )

    assert mistral_ai_chat_completion.ai_model_id == "overwrite_model_id"
    assert mistral_ai_chat_completion.async_client._api_key == "overwrite_api_key"
    assert isinstance(mistral_ai_chat_completion, ChatCompletionClientBase)


@pytest.mark.parametrize("exclude_list", [["MISTRALAI_API_KEY", "MISTRALAI_CHAT_MODEL_ID"]], indirect=True)
def test_mistral_ai_chat_completion_init_constructor_missing_model(mistralai_unit_test_env) -> None:
    # Test successful initialization
    with pytest.raises(ServiceInitializationError):
        MistralAIChatCompletion(api_key="overwrite_api_key", env_file_path="test.env")


@pytest.mark.parametrize("exclude_list", [["MISTRALAI_API_KEY", "MISTRALAI_CHAT_MODEL_ID"]], indirect=True)
def test_mistral_ai_chat_completion_init_constructor_missing_api_key(mistralai_unit_test_env) -> None:
    # Test successful initialization
    with pytest.raises(ServiceInitializationError):
        MistralAIChatCompletion(ai_model_id="overwrite_model_id", env_file_path="test.env")


def test_mistral_ai_chat_completion_init_hybrid(mistralai_unit_test_env) -> None:
    mistral_ai_chat_completion = MistralAIChatCompletion(
        ai_model_id="overwrite_model_id",
        env_file_path="test.env",
    )
    assert mistral_ai_chat_completion.ai_model_id == "overwrite_model_id"
    assert mistral_ai_chat_completion.async_client._api_key == "test_api_key"


@pytest.mark.parametrize("exclude_list", [["MISTRALAI_CHAT_MODEL_ID"]], indirect=True)
def test_mistral_ai_chat_completion_init_with_empty_model_id(mistralai_unit_test_env) -> None:
    with pytest.raises(ServiceInitializationError):
        MistralAIChatCompletion(
            env_file_path="test.env",
        )


def test_prompt_execution_settings_class(mistralai_unit_test_env):
    mistral_ai_chat_completion = MistralAIChatCompletion()
    prompt_execution_settings = mistral_ai_chat_completion.get_prompt_execution_settings_class()
    assert prompt_execution_settings == MistralAIChatPromptExecutionSettings


@pytest.mark.asyncio
async def test_with_different_execution_settings(kernel: Kernel, mock_mistral_ai_client_completion: MagicMock):
    chat_history = MagicMock()
    settings = OpenAIChatPromptExecutionSettings(temperature=0.2, seed=2)
    arguments = KernelArguments()
    chat_completion_base = MistralAIChatCompletion(
        ai_model_id="test_model_id", service_id="test", api_key="", async_client=mock_mistral_ai_client_completion
    )

    await chat_completion_base.get_chat_message_contents(
        chat_history=chat_history, settings=settings, kernel=kernel, arguments=arguments
    )
    assert mock_mistral_ai_client_completion.chat.call_args.kwargs["temperature"] == 0.2
    assert mock_mistral_ai_client_completion.chat.call_args.kwargs["seed"] == 2


@pytest.mark.asyncio
async def test_with_different_execution_settings_stream(
    kernel: Kernel, mock_mistral_ai_client_completion_stream: MagicMock
):
    chat_history = MagicMock()
    settings = OpenAIChatPromptExecutionSettings(temperature=0.2, seed=2)
    arguments = KernelArguments()
    chat_completion_base = MistralAIChatCompletion(
        ai_model_id="test_model_id",
        service_id="test",
        api_key="",
        async_client=mock_mistral_ai_client_completion_stream,
    )

    async for chunk in chat_completion_base.get_streaming_chat_message_contents(
        chat_history, settings, kernel=kernel, arguments=arguments
    ):
        continue
    assert mock_mistral_ai_client_completion_stream.chat_stream.call_args.kwargs["temperature"] == 0.2
    assert mock_mistral_ai_client_completion_stream.chat_stream.call_args.kwargs["seed"] == 2
