# Copyright (c) Microsoft. All rights reserved.
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior, FunctionChoiceType
from semantic_kernel.connectors.ai.mistral_ai import MistralAIChatCompletion, MistralAIChatPromptExecutionSettings
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

pytestmark = pytest.mark.parametrize('completion_object , prompt_execution_settings , fake_tool_call', [
    pytest.param(
        MistralAIChatCompletion(),
        MistralAIChatPromptExecutionSettings(
            function_choice_behavior=FunctionChoiceBehavior.Auto()
        ),
        True,
        id="MistralToolProcessingTrueAutoInvoke"
    ),
    pytest.param(
        MistralAIChatCompletion(),
        MistralAIChatPromptExecutionSettings(
            function_choice_behavior=FunctionChoiceBehavior.Auto()
        ),
        False,
        id="MistralToolProcessingFalseAutoInvoke"
    ),
    pytest.param(
        MistralAIChatCompletion(),
        MistralAIChatPromptExecutionSettings(
            function_choice_behavior=FunctionChoiceBehavior.NoneInvoke()
        ),
        True,
        id="MistralToolProcessingTrueNoneInvoke"
    ),
    pytest.param(
        MistralAIChatCompletion(),
        MistralAIChatPromptExecutionSettings(
            function_choice_behavior=FunctionChoiceBehavior.NoneInvoke()
        ),
        False,
        id="MistralToolProcessingFalseNoneInvoke"
    ),
    pytest.param(
        MistralAIChatCompletion(),
        MistralAIChatPromptExecutionSettings(
            function_choice_behavior=FunctionChoiceBehavior.Required()
        ),
        True,
        id="MistralToolProcessingTrueRequired"
    )
]
)


@pytest.mark.asyncio
async def test_function_call_processing_with_function_call_content_result(
    completion_object: ChatCompletionClientBase,
    prompt_execution_settings: PromptExecutionSettings,
    kernel: Kernel,
    fake_tool_call: bool
):

    arguments = KernelArguments()
    chat_history = ChatHistory(system_message="Test")

    mock_text = MagicMock(spec=TextContent)
    mock_message_text_content = ChatMessageContent(
        role=AuthorRole.ASSISTANT, items=[mock_text]
    )
    mock_function_call = MagicMock(spec=FunctionCallContent)
    mock_message_function_call = ChatMessageContent(
        role=AuthorRole.ASSISTANT, items=[mock_function_call]
    )

    if fake_tool_call:
        mock_messages = [[mock_message_function_call], [mock_message_text_content]]
    else:
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
        result = await completion_object.invoke(
            chat_history=chat_history,
            settings=prompt_execution_settings,
            kernel=kernel,
            arguments=arguments
        )

        if (
            prompt_execution_settings.function_choice_behavior.type is FunctionChoiceType.AUTO
            and fake_tool_call is True
        ):
            mock_process_function_call.assert_awaited()
            assert result == [mock_message_text_content]
        elif (
            prompt_execution_settings.function_choice_behavior.type is FunctionChoiceType.NONE
            and fake_tool_call is True 
        ):
            mock_process_function_call.assert_not_awaited()
            assert result == [mock_message_function_call]
        elif (
            prompt_execution_settings.function_choice_behavior.type is FunctionChoiceType.REQUIRED
            and fake_tool_call is True 
        ):
            mock_process_function_call.assert_awaited()
            assert result == [mock_message_text_content]
        else:
            assert result ==  [mock_message_text_content]
