# Copyright (c) Microsoft. All rights reserved.
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.azure_ai_inference import (
    AzureAIInferenceChatCompletion,
    AzureAIInferenceChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior, FunctionChoiceType
from semantic_kernel.connectors.ai.mistral_ai import MistralAIChatCompletion, MistralAIChatPromptExecutionSettings
from semantic_kernel.connectors.ai.ollama import OllamaChatCompletion, OllamaPromptExecutionSettings
from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import (
    ChatMessageContent,
    FunctionCallContent,
    FunctionResultContent,
    TextContent,
)
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.functions.kernel_arguments import KernelArguments

pytestmark = pytest.mark.parametrize('completion_object , prompt_execution_settings , function_calling_implemented', [
    pytest.param(
        MistralAIChatCompletion(),
        MistralAIChatPromptExecutionSettings(),
        True,
        id="mistral_none_settings"
    ),
    pytest.param(
        MistralAIChatCompletion(),
        MistralAIChatPromptExecutionSettings(
            function_choice_behavior=FunctionChoiceBehavior.Auto()
        ),
        True,
        id="mistral_tool_auto"
    ),
    pytest.param(
        MistralAIChatCompletion(),
        MistralAIChatPromptExecutionSettings(
            function_choice_behavior=FunctionChoiceBehavior.Required()
        ),
        True,
        id="mistral_tool_required"
    ),
    pytest.param(
        MistralAIChatCompletion(),
        MistralAIChatPromptExecutionSettings(
            function_choice_behavior=FunctionChoiceBehavior.NoneInvoke()
        ),
        True,
        id="mistral_tool_none_invoke"
    ),
    pytest.param(
        AzureAIInferenceChatCompletion(ai_model_id="test"),
        AzureAIInferenceChatPromptExecutionSettings(),
        False,
        id="azure_ai_inference_none_settings"
    ),
    pytest.param(
        AzureAIInferenceChatCompletion(ai_model_id="test"),
        AzureAIInferenceChatPromptExecutionSettings(
            function_choice_behavior=FunctionChoiceBehavior.NoneInvoke()
        ),
        False,
        id="azure_ai_inference_not_implemented"
    ),
    pytest.param(
        OllamaChatCompletion(ai_model_id="test"),
        OllamaPromptExecutionSettings(), 
        False,
        id="ollama_none_settings"
    ),
    pytest.param(
        OllamaChatCompletion(ai_model_id="test"),
        OllamaPromptExecutionSettings(
            function_choice_behavior=FunctionChoiceBehavior.NoneInvoke()
        ),
        False,
        id="ollama_not_implemented"
    ),
]
)


@pytest.mark.asyncio
async def test_invoke_function_call_processing_with_function_call_content_result(
    completion_object: ChatCompletionClientBase,
    prompt_execution_settings: PromptExecutionSettings,
    function_calling_implemented: bool,
    kernel: Kernel
):
    # Prepare Connector Mocks
    mock_text = MagicMock(spec=TextContent)
    mock_message_text_content = ChatMessageContent(
        role=AuthorRole.ASSISTANT, items=[mock_text]
    )
    mock_function_call = MagicMock(spec=FunctionCallContent)
    mock_message_function_call = ChatMessageContent(
        role=AuthorRole.ASSISTANT, items=[mock_function_call]
    )

    if (
        prompt_execution_settings.function_choice_behavior is not None
        and prompt_execution_settings.function_choice_behavior.type is not FunctionChoiceType.NONE
    ):
        # Mock Tool Flow FunctionCall --> FunctionResult --> TextContent
        mock_messages = [[mock_message_function_call], [mock_message_text_content]]
    else:
        # Mock None Flow TextContent
        mock_messages = [[mock_message_text_content]]

    def fake_function_result(
            function_call,
            chat_history: ChatHistory,
            arguments,
            function_call_count,
            request_index,
            function_behavior,
    ):
        mock_function_result = MagicMock(spec=FunctionResultContent)
        mock_message_function_result = ChatMessageContent(
            role=AuthorRole.TOOL, items=[mock_function_result]
        )
        chat_history.add_message(message=mock_message_function_result)
        return

    with (
        patch.object(
            completion_object.__class__, 
            'get_chat_message_contents',
              side_effect=mock_messages),
        patch(
            "semantic_kernel.kernel.Kernel.invoke_function_call",
            side_effect=fake_function_result,
            new_callable=AsyncMock,
            
        ) as mock_process_function_call,
    ):
        # Check for Proper Error when function Calling is not implemented
        if not function_calling_implemented and prompt_execution_settings.function_choice_behavior is not None:
            with pytest.raises(NotImplementedError):
                await completion_object.invoke(
                    chat_history=ChatHistory(system_message="Test"),
                    settings=prompt_execution_settings,
                    kernel=kernel,
                    arguments=KernelArguments()
                )
            return

        result = await completion_object.invoke(
            chat_history=ChatHistory(system_message="Test"),
            settings=prompt_execution_settings,
            kernel=kernel,
            arguments=KernelArguments()
        )

        # Flow without Function Choice Settings should return TextContent
        if prompt_execution_settings.function_choice_behavior is None:
            assert result == [mock_message_text_content]
            return

        # Full Automation Flow should return TextContent
        if prompt_execution_settings.function_choice_behavior.type is not FunctionChoiceType.NONE:
            mock_process_function_call.assert_awaited()
        else:
            mock_process_function_call.assert_not_awaited()
        assert result == [mock_message_text_content]


@pytest.mark.asyncio
async def test_invoke_function_call_processing_with_text_content_content_result(
    completion_object: ChatCompletionClientBase,
    prompt_execution_settings: PromptExecutionSettings,
    function_calling_implemented: bool,
    kernel: Kernel,
):
    
    arguments = KernelArguments()
    chat_history = ChatHistory(system_message="Test")

    mock_text = MagicMock(spec=TextContent)
    mock_message_text_content = ChatMessageContent(
        role=AuthorRole.ASSISTANT, items=[mock_text]
    )
    mock_messages = [[mock_message_text_content]]

    with (
        patch.object(
            completion_object.__class__, 
            'get_chat_message_contents',
              side_effect=mock_messages),
    ):
        # Check for Proper Error when function Calling is not implemented
        if not function_calling_implemented and prompt_execution_settings.function_choice_behavior is not None:
            with pytest.raises(NotImplementedError):
                await completion_object.invoke(
                    chat_history=ChatHistory(system_message="Test"),
                    settings=prompt_execution_settings,
                    kernel=kernel,
                    arguments=KernelArguments()
                )
            return

        result = await completion_object.invoke(
            chat_history=chat_history,
            settings=prompt_execution_settings,
            kernel=kernel,
            arguments=arguments
        )
        assert result == [mock_message_text_content]
