# Copyright (c) Microsoft. All rights reserved.

from unittest.mock import AsyncMock, patch

import pytest
from azure.ai.inference.aio import ChatCompletionsClient
from azure.ai.inference.models import JsonSchemaFormat, UserMessage
from azure.core.credentials import AzureKeyCredential
from pydantic import BaseModel, Field

from semantic_kernel.connectors.ai.azure_ai_inference import (
    AzureAIInferenceChatCompletion,
    AzureAIInferenceChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.azure_ai_inference.azure_ai_inference_settings import AzureAIInferenceSettings
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.utils.finish_reason import FinishReason
from semantic_kernel.exceptions.service_exceptions import (
    ServiceInitializationError,
    ServiceInvalidExecutionSettingsError,
)
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.kernel import Kernel
from semantic_kernel.utils.telemetry.user_agent import SEMANTIC_KERNEL_USER_AGENT


# region init
def test_azure_ai_inference_chat_completion_init(azure_ai_inference_unit_test_env, model_id) -> None:
    """Test initialization of AzureAIInferenceChatCompletion"""
    azure_ai_inference = AzureAIInferenceChatCompletion(model_id, instruction_role="developer")

    assert azure_ai_inference.ai_model_id == model_id
    assert azure_ai_inference.service_id == model_id
    assert isinstance(azure_ai_inference.client, ChatCompletionsClient)
    assert azure_ai_inference.instruction_role == "developer"


@patch("azure.ai.inference.aio.ChatCompletionsClient.__init__", return_value=None)
def test_azure_ai_inference_chat_completion_client_init(
    mock_client, azure_ai_inference_unit_test_env, model_id
) -> None:
    """Test initialization of the Azure AI Inference client"""
    endpoint = azure_ai_inference_unit_test_env["AZURE_AI_INFERENCE_ENDPOINT"]
    api_key = azure_ai_inference_unit_test_env["AZURE_AI_INFERENCE_API_KEY"]
    settings = AzureAIInferenceSettings(endpoint=endpoint, api_key=api_key)

    _ = AzureAIInferenceChatCompletion(model_id)

    assert mock_client.call_count == 1
    assert isinstance(mock_client.call_args.kwargs["endpoint"], str)
    assert mock_client.call_args.kwargs["endpoint"] == str(settings.endpoint)
    assert isinstance(mock_client.call_args.kwargs["credential"], AzureKeyCredential)
    assert mock_client.call_args.kwargs["credential"].key == settings.api_key.get_secret_value()
    assert mock_client.call_args.kwargs["user_agent"] == SEMANTIC_KERNEL_USER_AGENT


def test_azure_ai_inference_chat_completion_init_with_service_id(
    azure_ai_inference_unit_test_env, model_id, service_id
) -> None:
    """Test initialization of AzureAIInferenceChatCompletion with service_id"""
    azure_ai_inference = AzureAIInferenceChatCompletion(model_id, service_id=service_id)

    assert azure_ai_inference.ai_model_id == model_id
    assert azure_ai_inference.service_id == service_id
    assert isinstance(azure_ai_inference.client, ChatCompletionsClient)


@pytest.mark.parametrize(
    "azure_ai_inference_client",
    [AzureAIInferenceChatCompletion.__name__],
    indirect=True,
)
def test_azure_ai_inference_chat_completion_init_with_custom_client(azure_ai_inference_client, model_id) -> None:
    """Test initialization of AzureAIInferenceChatCompletion with custom client"""
    client = azure_ai_inference_client
    azure_ai_inference = AzureAIInferenceChatCompletion(model_id, client=client)

    assert azure_ai_inference.ai_model_id == model_id
    assert azure_ai_inference.service_id == model_id
    assert azure_ai_inference.client == client


@pytest.mark.parametrize("exclude_list", [["AZURE_AI_INFERENCE_ENDPOINT"]], indirect=True)
def test_azure_ai_inference_chat_completion_init_with_empty_endpoint(
    azure_ai_inference_unit_test_env, model_id
) -> None:
    """Test initialization of AzureAIInferenceChatCompletion with empty endpoint"""
    with pytest.raises(ServiceInitializationError):
        AzureAIInferenceChatCompletion(model_id, env_file_path="fake_path")


def test_prompt_execution_settings_class(azure_ai_inference_unit_test_env, model_id) -> None:
    azure_ai_inference = AzureAIInferenceChatCompletion(model_id)
    assert azure_ai_inference.get_prompt_execution_settings_class() == AzureAIInferenceChatPromptExecutionSettings


# endregion init


# region chat completion


@pytest.mark.parametrize(
    "azure_ai_inference_service",
    [AzureAIInferenceChatCompletion.__name__],
    indirect=True,
)
@patch.object(ChatCompletionsClient, "complete", new_callable=AsyncMock)
async def test_azure_ai_inference_chat_completion(
    mock_complete,
    azure_ai_inference_service,
    model_id,
    chat_history: ChatHistory,
    mock_azure_ai_inference_chat_completion_response,
) -> None:
    """Test completion of AzureAIInferenceChatCompletion"""
    user_message_content: str = "Hello"
    chat_history.add_user_message(user_message_content)
    settings = AzureAIInferenceChatPromptExecutionSettings()

    mock_complete.return_value = mock_azure_ai_inference_chat_completion_response

    responses = await azure_ai_inference_service.get_chat_message_contents(chat_history=chat_history, settings=settings)

    mock_complete.assert_awaited_once_with(
        messages=[UserMessage(content=user_message_content)],
        model=model_id,
        model_extras=None,
        **settings.prepare_settings_dict(),
    )
    assert len(responses) == 1
    assert responses[0].role == "assistant"
    assert responses[0].content == "Hello"


@pytest.mark.parametrize(
    "azure_ai_inference_service",
    [AzureAIInferenceChatCompletion.__name__],
    indirect=True,
)
@patch.object(ChatCompletionsClient, "complete", new_callable=AsyncMock)
async def test_azure_ai_inference_chat_completion_with_standard_parameters(
    mock_complete,
    azure_ai_inference_service,
    model_id,
    chat_history: ChatHistory,
    mock_azure_ai_inference_chat_completion_response,
) -> None:
    """Test completion of AzureAIInferenceChatCompletion with standard OpenAI parameters"""
    user_message_content: str = "Hello"
    chat_history.add_user_message(user_message_content)

    settings = AzureAIInferenceChatPromptExecutionSettings(
        frequency_penalty=0.5,
        max_tokens=100,
        presence_penalty=0.5,
        seed=123,
        stop="stop",
        temperature=0.5,
        top_p=0.5,
    )

    mock_complete.return_value = mock_azure_ai_inference_chat_completion_response

    responses = await azure_ai_inference_service.get_chat_message_contents(chat_history=chat_history, settings=settings)

    mock_complete.assert_awaited_once_with(
        messages=[UserMessage(content=user_message_content)],
        model=model_id,
        model_extras=None,
        frequency_penalty=settings.frequency_penalty,
        max_tokens=settings.max_tokens,
        presence_penalty=settings.presence_penalty,
        seed=settings.seed,
        stop=settings.stop,
        temperature=settings.temperature,
        top_p=settings.top_p,
    )
    assert len(responses) == 1
    assert responses[0].role == "assistant"
    assert responses[0].content == "Hello"


@pytest.mark.parametrize(
    "azure_ai_inference_service",
    [AzureAIInferenceChatCompletion.__name__],
    indirect=True,
)
@patch.object(ChatCompletionsClient, "complete", new_callable=AsyncMock)
async def test_azure_ai_inference_chat_completion_with_extra_parameters(
    mock_complete,
    azure_ai_inference_service,
    model_id,
    chat_history: ChatHistory,
    mock_azure_ai_inference_chat_completion_response,
) -> None:
    """Test completion of AzureAIInferenceChatCompletion with extra parameters"""
    user_message_content: str = "Hello"
    chat_history.add_user_message(user_message_content)
    extra_parameters = {"test_key": "test_value"}

    settings = AzureAIInferenceChatPromptExecutionSettings(extra_parameters=extra_parameters)

    mock_complete.return_value = mock_azure_ai_inference_chat_completion_response

    responses = await azure_ai_inference_service.get_chat_message_contents(chat_history=chat_history, settings=settings)

    mock_complete.assert_awaited_once_with(
        messages=[UserMessage(content=user_message_content)],
        model=model_id,
        model_extras=settings.extra_parameters,
        **settings.prepare_settings_dict(),
    )
    assert len(responses) == 1
    assert responses[0].role == "assistant"
    assert responses[0].content == "Hello"


@pytest.mark.parametrize(
    "azure_ai_inference_service",
    [AzureAIInferenceChatCompletion.__name__],
    indirect=True,
)
async def test_azure_ai_inference_chat_completion_with_function_choice_behavior_fail_verification(
    azure_ai_inference_service,
    kernel,
    chat_history: ChatHistory,
) -> None:
    """Test completion of AzureAIInferenceChatCompletion with function choice behavior expect verification failure"""

    # Missing kernel
    with pytest.raises(ServiceInvalidExecutionSettingsError):
        settings = AzureAIInferenceChatPromptExecutionSettings(
            function_choice_behavior=FunctionChoiceBehavior.Auto(),
        )
        await azure_ai_inference_service.get_chat_message_contents(
            chat_history=chat_history,
            settings=settings,
            arguments=KernelArguments(),
        )

    # More than 1 responses
    with pytest.raises(ServiceInvalidExecutionSettingsError):
        settings = AzureAIInferenceChatPromptExecutionSettings(
            function_choice_behavior=FunctionChoiceBehavior.Auto(),
            extra_parameters={"n": 2},
        )
        await azure_ai_inference_service.get_chat_message_contents(
            chat_history=chat_history,
            settings=settings,
            kernel=kernel,
            arguments=KernelArguments(),
        )


@pytest.mark.parametrize(
    "azure_ai_inference_service",
    [AzureAIInferenceChatCompletion.__name__],
    indirect=True,
)
@patch.object(ChatCompletionsClient, "complete", new_callable=AsyncMock)
async def test_azure_ai_inference_chat_completion_with_function_choice_behavior(
    mock_complete,
    azure_ai_inference_service,
    kernel,
    chat_history: ChatHistory,
    mock_azure_ai_inference_chat_completion_response_with_tool_call,
) -> None:
    """Test completion of AzureAIInferenceChatCompletion with function choice behavior"""
    user_message_content: str = "Hello"
    chat_history.add_user_message(user_message_content)

    settings = AzureAIInferenceChatPromptExecutionSettings(
        function_choice_behavior=FunctionChoiceBehavior.Auto(),
    )
    settings.function_choice_behavior.maximum_auto_invoke_attempts = 1

    mock_complete.return_value = mock_azure_ai_inference_chat_completion_response_with_tool_call

    responses = await azure_ai_inference_service.get_chat_message_contents(
        chat_history=chat_history,
        settings=settings,
        kernel=kernel,
        arguments=KernelArguments(),
    )

    # The function should be called twice:
    # One for the tool call and one for the last completion
    # after the maximum_auto_invoke_attempts is reached
    assert mock_complete.call_count == 2
    assert len(responses) == 1
    assert responses[0].role == "assistant"
    assert responses[0].finish_reason == FinishReason.TOOL_CALLS


@pytest.mark.parametrize(
    "azure_ai_inference_service",
    [AzureAIInferenceChatCompletion.__name__],
    indirect=True,
)
@patch.object(ChatCompletionsClient, "complete", new_callable=AsyncMock)
async def test_azure_ai_inference_chat_completion_with_function_choice_behavior_no_tool_call(
    mock_complete,
    azure_ai_inference_service,
    model_id,
    kernel,
    chat_history: ChatHistory,
    mock_azure_ai_inference_chat_completion_response,
) -> None:
    """Test completion of AzureAIInferenceChatCompletion with function choice behavior but no tool call"""
    user_message_content: str = "Hello"
    chat_history.add_user_message(user_message_content)

    settings = AzureAIInferenceChatPromptExecutionSettings(
        function_choice_behavior=FunctionChoiceBehavior.Auto(),
    )

    mock_complete.return_value = mock_azure_ai_inference_chat_completion_response

    responses = await azure_ai_inference_service.get_chat_message_contents(
        chat_history=chat_history,
        settings=settings,
        kernel=kernel,
        arguments=KernelArguments(),
    )

    mock_complete.assert_awaited_once_with(
        messages=[UserMessage(content=user_message_content)],
        model=model_id,
        model_extras=None,
        **settings.prepare_settings_dict(),
    )
    assert len(responses) == 1
    assert responses[0].role == "assistant"
    assert responses[0].content == "Hello"


class MockResponseModel(BaseModel):
    a: int = Field(..., description="The a field")
    b: str = Field(..., description="The b field")


@pytest.mark.parametrize(
    "azure_ai_inference_service",
    [AzureAIInferenceChatCompletion.__name__],
    indirect=True,
)
@patch.object(ChatCompletionsClient, "complete", new_callable=AsyncMock)
async def test_azure_ai_inference_response_format_json_schema(
    mock_complete,
    azure_ai_inference_service,
    model_id,
    chat_history: ChatHistory,
    mock_azure_ai_inference_chat_completion_response,
):
    chat_history.add_user_message("Return an object with fields a and b.")
    settings = AzureAIInferenceChatPromptExecutionSettings(
        response_format=MockResponseModel,
        structured_json_response=True,
    )

    mock_complete.return_value = mock_azure_ai_inference_chat_completion_response

    _ = await azure_ai_inference_service.get_chat_message_contents(chat_history=chat_history, settings=settings)

    assert mock_complete.call_count == 1
    kwargs = mock_complete.call_args.kwargs

    assert "response_format" in kwargs
    response_format = kwargs["response_format"]
    assert isinstance(response_format, JsonSchemaFormat)
    assert response_format.name == "MockResponseModel"
    assert response_format.strict is True

    schema = response_format.schema
    assert schema["title"] == "MockResponseModel"
    assert "properties" in schema
    assert "a" in schema["properties"]
    assert schema["properties"]["a"]["type"] == "integer"
    assert "b" in schema["properties"]
    assert schema["properties"]["b"]["type"] == "string"

    assert kwargs["messages"][0].content == "Return an object with fields a and b."
    assert kwargs["model"] == model_id


# endregion chat completion


# region streaming chat completion


@pytest.mark.parametrize(
    "azure_ai_inference_service",
    [AzureAIInferenceChatCompletion.__name__],
    indirect=True,
)
@patch.object(ChatCompletionsClient, "complete", new_callable=AsyncMock)
async def test_azure_ai_inference_streaming_chat_completion(
    mock_complete,
    azure_ai_inference_service,
    model_id,
    chat_history: ChatHistory,
    mock_azure_ai_inference_streaming_chat_completion_response,
) -> None:
    """Test streaming completion of AzureAIInferenceChatCompletion"""
    user_message_content: str = "Hello"
    chat_history.add_user_message(user_message_content)
    settings = AzureAIInferenceChatPromptExecutionSettings()

    mock_complete.return_value = mock_azure_ai_inference_streaming_chat_completion_response

    async for messages in azure_ai_inference_service.get_streaming_chat_message_contents(chat_history, settings):
        assert len(messages) == 1
        assert messages[0].role == "assistant"
        assert messages[0].content == "Hello"

    mock_complete.assert_awaited_once_with(
        stream=True,
        messages=[UserMessage(content=user_message_content)],
        model=model_id,
        model_extras=None,
        **settings.prepare_settings_dict(),
    )


@pytest.mark.parametrize(
    "azure_ai_inference_service",
    [AzureAIInferenceChatCompletion.__name__],
    indirect=True,
)
@patch.object(ChatCompletionsClient, "complete", new_callable=AsyncMock)
async def test_azure_ai_inference_chat_streaming_completion_with_standard_parameters(
    mock_complete,
    azure_ai_inference_service,
    model_id,
    chat_history: ChatHistory,
    mock_azure_ai_inference_streaming_chat_completion_response,
) -> None:
    """Test streaming completion of AzureAIInferenceChatCompletion with standard OpenAI parameters"""
    user_message_content: str = "Hello"
    chat_history.add_user_message(user_message_content)

    settings = AzureAIInferenceChatPromptExecutionSettings(
        frequency_penalty=0.5,
        max_tokens=100,
        presence_penalty=0.5,
        seed=123,
        stop="stop",
        temperature=0.5,
        top_p=0.5,
    )

    mock_complete.return_value = mock_azure_ai_inference_streaming_chat_completion_response

    async for messages in azure_ai_inference_service.get_streaming_chat_message_contents(chat_history, settings):
        assert len(messages) == 1
        assert messages[0].role == "assistant"
        assert messages[0].content == "Hello"

    mock_complete.assert_awaited_once_with(
        stream=True,
        messages=[UserMessage(content=user_message_content)],
        model=model_id,
        model_extras=None,
        frequency_penalty=settings.frequency_penalty,
        max_tokens=settings.max_tokens,
        presence_penalty=settings.presence_penalty,
        seed=settings.seed,
        stop=settings.stop,
        temperature=settings.temperature,
        top_p=settings.top_p,
    )


@pytest.mark.parametrize(
    "azure_ai_inference_service",
    [AzureAIInferenceChatCompletion.__name__],
    indirect=True,
)
@patch.object(ChatCompletionsClient, "complete", new_callable=AsyncMock)
async def test_azure_ai_inference_streaming_chat_completion_with_extra_parameters(
    mock_complete,
    azure_ai_inference_service,
    model_id,
    chat_history: ChatHistory,
    mock_azure_ai_inference_streaming_chat_completion_response,
) -> None:
    """Test streaming completion of AzureAIInferenceChatCompletion with extra parameters"""
    user_message_content: str = "Hello"
    chat_history.add_user_message(user_message_content)
    extra_parameters = {"test_key": "test_value"}

    settings = AzureAIInferenceChatPromptExecutionSettings(extra_parameters=extra_parameters)

    mock_complete.return_value = mock_azure_ai_inference_streaming_chat_completion_response

    async for messages in azure_ai_inference_service.get_streaming_chat_message_contents(chat_history, settings):
        assert len(messages) == 1
        assert messages[0].role == "assistant"
        assert messages[0].content == "Hello"

    mock_complete.assert_awaited_once_with(
        stream=True,
        messages=[UserMessage(content=user_message_content)],
        model=model_id,
        model_extras=settings.extra_parameters,
        **settings.prepare_settings_dict(),
    )


@pytest.mark.parametrize(
    "azure_ai_inference_service",
    [AzureAIInferenceChatCompletion.__name__],
    indirect=True,
)
async def test_azure_ai_inference_streaming_chat_completion_with_function_choice_behavior_fail_verification(
    azure_ai_inference_service,
    kernel,
    chat_history: ChatHistory,
) -> None:
    """Test completion of AzureAIInferenceChatCompletion with function choice behavior expect verification failure"""

    # Missing kernel
    with pytest.raises(ServiceInvalidExecutionSettingsError):
        settings = AzureAIInferenceChatPromptExecutionSettings(
            function_choice_behavior=FunctionChoiceBehavior.Auto(),
        )
        async for _ in azure_ai_inference_service.get_streaming_chat_message_contents(
            chat_history,
            settings,
            arguments=KernelArguments(),
        ):
            pass

    # More than 1 responses
    with pytest.raises(ServiceInvalidExecutionSettingsError):
        settings = AzureAIInferenceChatPromptExecutionSettings(
            function_choice_behavior=FunctionChoiceBehavior.Auto(),
            extra_parameters={"n": 2},
        )
        async for _ in azure_ai_inference_service.get_streaming_chat_message_contents(
            chat_history,
            settings,
            kernel=kernel,
            arguments=KernelArguments(),
        ):
            pass


@pytest.mark.parametrize(
    "azure_ai_inference_service",
    [AzureAIInferenceChatCompletion.__name__],
    indirect=True,
)
@patch.object(ChatCompletionsClient, "complete", new_callable=AsyncMock)
async def test_azure_ai_inference_streaming_chat_completion_with_function_choice_behavior(
    mock_complete,
    azure_ai_inference_service,
    kernel: Kernel,
    chat_history: ChatHistory,
    mock_azure_ai_inference_streaming_chat_completion_response_with_tool_call,
    decorated_native_function,
) -> None:
    """Test streaming completion of AzureAIInferenceChatCompletion with function choice behavior."""
    user_message_content: str = "Hello"
    chat_history.add_user_message(user_message_content)

    settings = AzureAIInferenceChatPromptExecutionSettings(
        function_choice_behavior=FunctionChoiceBehavior.Auto(),
    )
    settings.function_choice_behavior.maximum_auto_invoke_attempts = 1

    mock_complete.return_value = mock_azure_ai_inference_streaming_chat_completion_response_with_tool_call

    kernel.add_function(plugin_name="TestPlugin", function=decorated_native_function)

    all_messages = []
    async for messages in azure_ai_inference_service.get_streaming_chat_message_contents(
        chat_history,
        settings,
        kernel=kernel,
        arguments=KernelArguments(),
    ):
        all_messages.extend(messages)

    # Assert the number of total messages
    assert len(all_messages) == 2, f"Expected 2 messages, got {len(all_messages)}"

    # Validate the first message
    assert all_messages[0].role == "assistant", f"Unexpected role for first message: {all_messages[0].role}"
    assert all_messages[0].content == "", f"Unexpected content for first message: {all_messages[0].content}"
    assert all_messages[0].finish_reason == FinishReason.TOOL_CALLS, (
        f"Unexpected finish reason for first message: {all_messages[0].finish_reason}"
    )

    # Validate the second message
    assert all_messages[1].role == "tool", f"Unexpected role for second message: {all_messages[1].role}"
    assert all_messages[1].content == "", f"Unexpected content for second message: {all_messages[1].content}"
    assert all_messages[1].finish_reason is None


@pytest.mark.parametrize(
    "azure_ai_inference_service",
    [AzureAIInferenceChatCompletion.__name__],
    indirect=True,
)
@patch.object(ChatCompletionsClient, "complete", new_callable=AsyncMock)
async def test_azure_ai_inference_streaming_chat_completion_with_function_choice_behavior_no_tool_call(
    mock_complete,
    azure_ai_inference_service,
    model_id,
    kernel,
    chat_history: ChatHistory,
    mock_azure_ai_inference_streaming_chat_completion_response,
) -> None:
    """Test streaming completion of AzureAIInferenceChatCompletion with function choice behavior but no tool call"""
    user_message_content: str = "Hello"
    chat_history.add_user_message(user_message_content)

    settings = AzureAIInferenceChatPromptExecutionSettings(
        function_choice_behavior=FunctionChoiceBehavior.Auto(),
    )

    mock_complete.return_value = mock_azure_ai_inference_streaming_chat_completion_response

    async for messages in azure_ai_inference_service.get_streaming_chat_message_contents(
        chat_history,
        settings,
        kernel=kernel,
        arguments=KernelArguments(),
    ):
        assert len(messages) == 1
        assert messages[0].role == "assistant"
        assert messages[0].content == "Hello"

    mock_complete.assert_awaited_once_with(
        stream=True,
        messages=[UserMessage(content=user_message_content)],
        model=model_id,
        model_extras=None,
        **settings.prepare_settings_dict(),
    )


class MockStreamingResponseModel(BaseModel):
    foo: float = Field(..., description="Foo value")
    bar: bool = Field(..., description="Bar value")


@pytest.mark.parametrize(
    "azure_ai_inference_service",
    [AzureAIInferenceChatCompletion.__name__],
    indirect=True,
)
@patch.object(ChatCompletionsClient, "complete", new_callable=AsyncMock)
async def test_azure_ai_inference_streaming_response_format_json_schema(
    mock_complete,
    azure_ai_inference_service,
    model_id,
    chat_history: ChatHistory,
    mock_azure_ai_inference_streaming_chat_completion_response,
):
    chat_history.add_user_message("Stream a response with foo and bar.")
    settings = AzureAIInferenceChatPromptExecutionSettings(
        response_format=MockStreamingResponseModel,
        structured_json_response=True,
    )

    mock_complete.return_value = mock_azure_ai_inference_streaming_chat_completion_response

    messages = []
    async for chunk in azure_ai_inference_service.get_streaming_chat_message_contents(chat_history, settings):
        messages.extend(chunk)

    assert mock_complete.call_count == 1
    kwargs = mock_complete.call_args.kwargs
    assert "response_format" in kwargs
    response_format = kwargs["response_format"]
    assert isinstance(response_format, JsonSchemaFormat)
    assert response_format.name == "MockStreamingResponseModel"
    assert response_format.strict is True
    schema = response_format.schema
    assert schema["title"] == "MockStreamingResponseModel"
    assert "foo" in schema["properties"]
    assert schema["properties"]["foo"]["type"] == "number"
    assert "bar" in schema["properties"]
    assert schema["properties"]["bar"]["type"] == "boolean"
    assert kwargs["stream"] is True
    assert kwargs["model"] == model_id


# endregion streaming chat completion
