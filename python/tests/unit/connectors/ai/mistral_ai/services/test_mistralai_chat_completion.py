# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from mistralai import CompletionEvent, Mistral
from mistralai.models import (
    AssistantMessage,
    ChatCompletionChoice,
    ChatCompletionResponse,
    CompletionChunk,
    CompletionResponseStreamChoice,
    DeltaMessage,
    UsageInfo,
)

from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.function_call_choice_configuration import FunctionCallChoiceConfiguration
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior, FunctionChoiceType
from semantic_kernel.connectors.ai.mistral_ai.prompt_execution_settings.mistral_ai_prompt_execution_settings import (
    MistralAIChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.mistral_ai.services.mistral_ai_chat_completion import MistralAIChatCompletion
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIChatPromptExecutionSettings,
)
from semantic_kernel.contents import FunctionCallContent, TextContent
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import (
    ChatMessageContent,
)
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.exceptions import (
    ServiceInitializationError,
    ServiceInvalidExecutionSettingsError,
    ServiceResponseException,
)
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.kernel import Kernel


@pytest.fixture
def mock_settings() -> MistralAIChatPromptExecutionSettings:
    return MistralAIChatPromptExecutionSettings()


@pytest.fixture
def mock_mistral_ai_client_completion() -> Mistral:
    client = MagicMock(spec=Mistral)
    client.chat = AsyncMock()

    chat_completion_response = AsyncMock()
    choices = [MagicMock(finish_reason="stop", message=MagicMock(role="assistant", content="Test"))]
    chat_completion_response.choices = choices
    client.chat.complete_async.return_value = chat_completion_response
    return client


@pytest.fixture
def mock_mistral_ai_client_completion_stream() -> Mistral:
    client = MagicMock(spec=Mistral)
    client.chat = AsyncMock()
    chat_completion_response = MagicMock()
    choices = [
        MagicMock(finish_reason="stop", delta=MagicMock(role="assistant", content="Test")),
        MagicMock(finish_reason="stop", delta=MagicMock(role="assistant", content="Test", tool_calls=None)),
    ]
    chat_completion_response.data.choices = choices
    chat_completion_response_empty = MagicMock()
    chat_completion_response_empty.choices = []
    generator_mock = MagicMock()
    generator_mock.__aiter__.return_value = [chat_completion_response_empty, chat_completion_response]
    client.chat.stream_async.return_value = generator_mock
    return client


async def test_complete_chat_contents(
    kernel: Kernel,
    mock_settings: MistralAIChatPromptExecutionSettings,
    mock_mistral_ai_client_completion: Mistral,
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


async def test_complete_chat_contents_function_call_behavior_without_kernel(
    mock_settings: MistralAIChatPromptExecutionSettings,
    mock_mistral_ai_client_completion: Mistral,
):
    chat_history = MagicMock()
    chat_completion_base = MistralAIChatCompletion(
        ai_model_id="test_model_id", service_id="test", api_key="", async_client=mock_mistral_ai_client_completion
    )

    mock_settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

    with pytest.raises(ServiceInvalidExecutionSettingsError):
        await chat_completion_base.get_chat_message_contents(chat_history=chat_history, settings=mock_settings)


async def test_complete_chat_stream_contents(
    kernel: Kernel,
    mock_settings: MistralAIChatPromptExecutionSettings,
    mock_mistral_ai_client_completion_stream: Mistral,
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


async def test_mistral_ai_sdk_exception(kernel: Kernel, mock_settings: MistralAIChatPromptExecutionSettings):
    chat_history = MagicMock()
    arguments = KernelArguments()
    client = MagicMock(spec=Mistral)
    client.chat = MagicMock()
    client.chat.complete_async.side_effect = Exception("Test Exception")

    chat_completion_base = MistralAIChatCompletion(
        ai_model_id="test_model_id", service_id="test", api_key="", async_client=client
    )

    with pytest.raises(ServiceResponseException):
        await chat_completion_base.get_chat_message_contents(
            chat_history=chat_history, settings=mock_settings, kernel=kernel, arguments=arguments
        )


async def test_mistral_ai_sdk_exception_streaming(kernel: Kernel, mock_settings: MistralAIChatPromptExecutionSettings):
    chat_history = MagicMock()
    arguments = KernelArguments()
    client = MagicMock(spec=Mistral)
    client.chat = MagicMock()
    client.chat.chat_stream.side_effect = Exception("Test Exception")

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
    api_key = mistralai_unit_test_env["MISTRALAI_API_KEY"]
    assert mistral_ai_chat_completion.async_client.sdk_configuration.security.api_key == api_key
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
    assert mistral_ai_chat_completion.async_client.sdk_configuration.security.api_key == "overwrite_api_key"
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
    assert mistral_ai_chat_completion.async_client.sdk_configuration.security.api_key == "test_api_key"


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
    assert mock_mistral_ai_client_completion.chat.complete_async.call_args.kwargs["temperature"] == 0.2
    assert mock_mistral_ai_client_completion.chat.complete_async.call_args.kwargs["seed"] == 2


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
    assert mock_mistral_ai_client_completion_stream.chat.stream_async.call_args.kwargs["temperature"] == 0.2
    assert mock_mistral_ai_client_completion_stream.chat.stream_async.call_args.kwargs["seed"] == 2


async def test_mistral_ai_chat_completion_get_chat_message_contents_success():
    """Test get_chat_message_contents with a successful ChatCompletionResponse."""

    # Mock the response from the Mistral chat complete_async.
    mock_response = ChatCompletionResponse(
        id="some_id",
        object="object",
        created=12345,
        usage=UsageInfo(prompt_tokens=10, completion_tokens=20, total_tokens=30),
        model="test-model",
        choices=[
            ChatCompletionChoice(
                index=0,
                message=AssistantMessage(role="assistant", content="Hello!"),
                finish_reason="stop",
            )
        ],
    )

    async_mock_client = MagicMock(spec=Mistral)
    async_mock_client.chat = MagicMock()
    async_mock_client.chat.complete_async = AsyncMock(return_value=mock_response)

    chat_completion = MistralAIChatCompletion(
        ai_model_id="test-model",
        api_key="test_key",
        async_client=async_mock_client,
    )

    # We create a ChatHistory.
    chat_history = ChatHistory()
    settings = MistralAIChatPromptExecutionSettings()

    results = await chat_completion.get_chat_message_contents(chat_history, settings)

    # We should have exactly one ChatMessageContent.
    assert len(results) == 1
    assert results[0].role.value == "assistant"
    assert results[0].finish_reason is not None
    assert results[0].finish_reason.value == "stop"
    assert "Hello!" in results[0].content
    async_mock_client.chat.complete_async.assert_awaited_once()


async def test_mistral_ai_chat_completion_get_chat_message_contents_failure():
    """Test get_chat_message_contents should raise ServiceResponseException if Mistral call fails."""
    async_mock_client = MagicMock(spec=Mistral)
    async_mock_client.chat = MagicMock()
    async_mock_client.chat.complete_async = AsyncMock(side_effect=Exception("API error"))

    chat_completion = MistralAIChatCompletion(
        ai_model_id="test-model",
        api_key="test_key",
        async_client=async_mock_client,
    )

    chat_history = ChatHistory()
    settings = MistralAIChatPromptExecutionSettings()

    with pytest.raises(ServiceResponseException) as exc:
        await chat_completion.get_chat_message_contents(chat_history, settings)
    assert "service failed to complete the prompt" in str(exc.value)


async def test_mistral_ai_chat_completion_get_streaming_chat_message_contents_success():
    """Test get_streaming_chat_message_contents when streaming successfully."""

    # We'll yield multiple chunks to simulate streaming.
    mock_chunk1 = CompletionEvent(
        data=CompletionChunk(
            id="chunk1",
            created=1,
            model="test-model",
            choices=[
                CompletionResponseStreamChoice(
                    index=0,
                    delta=DeltaMessage(role="assistant", content="Hello "),
                    finish_reason=None,
                )
            ],
        )
    )
    mock_chunk2 = CompletionEvent(
        data=CompletionChunk(
            id="chunk1",
            created=1,
            model="test-model",
            choices=[
                CompletionResponseStreamChoice(
                    index=0,
                    delta=DeltaMessage(content="World!"),
                    finish_reason="stop",
                )
            ],
        )
    )

    async def mock_stream_async(**kwargs):
        yield mock_chunk1
        yield mock_chunk2

    async_mock_client = MagicMock(spec=Mistral)
    async_mock_client.chat = MagicMock()
    async_mock_client.chat.stream_async = AsyncMock(return_value=mock_stream_async())

    chat_completion = MistralAIChatCompletion(
        ai_model_id="test-model",
        api_key="test_key",
        async_client=async_mock_client,
    )

    chat_history = ChatHistory()
    settings = MistralAIChatPromptExecutionSettings()

    collected_chunks = []
    async for chunk_list in chat_completion.get_streaming_chat_message_contents(chat_history, settings):
        collected_chunks.append(chunk_list)

    # We expect two sets of chunk_list yields.
    assert len(collected_chunks) == 2
    assert len(collected_chunks[0]) == 1
    assert len(collected_chunks[1]) == 1

    # First chunk contains "Hello ", second chunk "World!".
    assert collected_chunks[0][0].items[0].text == "Hello "
    assert collected_chunks[1][0].items[0].text == "World!"


async def test_mistral_ai_chat_completion_get_streaming_chat_message_contents_failure():
    """Test get_streaming_chat_message_contents raising a ServiceResponseException on failure."""
    async_mock_client = MagicMock(spec=Mistral)
    async_mock_client.chat = MagicMock()
    async_mock_client.chat.stream_async = AsyncMock(side_effect=Exception("Streaming error"))

    chat_completion = MistralAIChatCompletion(
        ai_model_id="test-model",
        api_key="test_key",
        async_client=async_mock_client,
    )

    chat_history = ChatHistory()
    settings = MistralAIChatPromptExecutionSettings()

    with pytest.raises(ServiceResponseException) as exc:
        async for _ in chat_completion.get_streaming_chat_message_contents(chat_history, settings):
            pass
    assert "service failed to complete the prompt" in str(exc.value)


async def test_mistral_ai_chat_completion_update_settings_from_function_call_configuration_mistral():
    """Test update_settings_from_function_call_configuration_mistral sets tools etc."""

    chat_completion = MistralAIChatCompletion(
        ai_model_id="test-model",
        api_key="test_key",
    )

    # Create a mock settings object.
    settings = MistralAIChatPromptExecutionSettings()
    # Create a function choice config with some available functions.
    config = FunctionCallChoiceConfiguration()
    mock_func = MagicMock(
        spec=KernelFunction,
    )
    mock_func.name = "my_func"
    mock_func.description = "some desc"
    mock_func.fully_qualified_name = "mod.my_func"
    mock_func.parameters = []
    config.available_functions = [mock_func]

    # Call the update_settings_from_function_call_configuration_mistral with type=ANY.
    chat_completion.update_settings_from_function_call_configuration_mistral(
        function_choice_configuration=config,
        settings=settings,
        type=FunctionChoiceType.AUTO,
    )

    assert settings.tool_choice == FunctionChoiceType.AUTO.value
    assert settings.tools is not None
    assert len(settings.tools) == 1
    assert settings.tools[0]["function"]["name"] == "mod.my_func"


async def test_mistral_ai_chat_completion_reset_function_choice_settings():
    """Test that _reset_function_choice_settings resets specific attributes."""
    chat_completion = MistralAIChatCompletion(
        ai_model_id="test-model",
        api_key="test_key",
    )
    settings = MistralAIChatPromptExecutionSettings(tool_choice="any", tools=[{"name": "func1"}])

    chat_completion._reset_function_choice_settings(settings)
    assert settings.tool_choice is None
    assert settings.tools is None


async def test_mistral_ai_chat_completion_service_url():
    """Test that service_url attempts to use _endpoint from the async_client."""
    async_mock_client = MagicMock(spec=Mistral)
    async_mock_client._endpoint = "mistral"

    chat_completion = MistralAIChatCompletion(
        ai_model_id="test-model",
        api_key="test_key",
        async_client=async_mock_client,
    )

    url = chat_completion.service_url()
    assert url == "mistral"
