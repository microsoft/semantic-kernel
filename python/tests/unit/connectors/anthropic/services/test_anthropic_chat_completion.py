# Copyright (c) Microsoft. All rights reserved.
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
from unittest.mock import AsyncMock, MagicMock
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
from unittest.mock import AsyncMock, MagicMock
=======
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock, MagicMock, patch
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head

import pytest
from anthropic import AsyncAnthropic
from anthropic.lib.streaming import TextEvent
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
from anthropic.types import (
    ContentBlockStopEvent,
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
from anthropic.types import (
    ContentBlockStopEvent,
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
from anthropic.types import (
    ContentBlockStopEvent,
=======
>>>>>>> Stashed changes
=======
from anthropic.types import (
    ContentBlockStopEvent,
=======
>>>>>>> Stashed changes
>>>>>>> head
from anthropic.lib.streaming._types import InputJsonEvent
from anthropic.types import (
    ContentBlockStopEvent,
    InputJSONDelta,
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    Message,
    MessageDeltaUsage,
    MessageStopEvent,
    RawContentBlockDeltaEvent,
    RawContentBlockStartEvent,
    RawMessageDeltaEvent,
    RawMessageStartEvent,
    TextBlock,
    TextDelta,
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
    ToolUseBlock,
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
    ToolUseBlock,
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
    ToolUseBlock,
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
    ToolUseBlock,
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    Usage,
)
from anthropic.types.raw_message_delta_event import Delta

from semantic_kernel.connectors.ai.anthropic.prompt_execution_settings.anthropic_prompt_execution_settings import (
    AnthropicChatPromptExecutionSettings,
)
from semantic_kernel.connectors.ai.anthropic.services.anthropic_chat_completion import AnthropicChatCompletion
from semantic_kernel.connectors.ai.chat_completion_client_base import ChatCompletionClientBase
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
from semantic_kernel.connectors.ai.function_choice_behavior import FunctionChoiceBehavior
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
from semantic_kernel.connectors.ai.open_ai.prompt_execution_settings.open_ai_prompt_execution_settings import (
    OpenAIChatPromptExecutionSettings,
)
from semantic_kernel.contents.chat_history import ChatHistory
from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.exceptions import ServiceInitializationError, ServiceResponseException
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
from semantic_kernel.functions.kernel_arguments import KernelArguments
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
from semantic_kernel.functions.kernel_arguments import KernelArguments
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
from semantic_kernel.functions.kernel_arguments import KernelArguments
=======
>>>>>>> Stashed changes
=======
from semantic_kernel.functions.kernel_arguments import KernelArguments
=======
>>>>>>> Stashed changes
>>>>>>> head
from semantic_kernel.contents.chat_message_content import (
    ChatMessageContent,
    FunctionCallContent,
    FunctionResultContent,
    TextContent,
)
from semantic_kernel.contents.const import ContentTypes
from semantic_kernel.contents.streaming_chat_message_content import StreamingChatMessageContent, StreamingTextContent
from semantic_kernel.contents.utils.author_role import AuthorRole
from semantic_kernel.contents.utils.finish_reason import FinishReason
from semantic_kernel.exceptions import (
    ServiceInitializationError,
    ServiceInvalidExecutionSettingsError,
    ServiceResponseException,
)
from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.functions.kernel_arguments import KernelArguments
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.functions.kernel_function_from_method import KernelFunctionMetadata
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
from semantic_kernel.kernel import Kernel


@pytest.fixture
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
def mock_tool_calls_message() -> ChatMessageContent:
    return ChatMessageContent(
        inner_content=Message(
            id="test_message_id",
            content=[
                TextBlock(text="<thinking></thinking>", type="text"),
                ToolUseBlock(
                    id="test_tool_use_blocks",
                    input={"input": 3, "amount": 3},
                    name="math-Add",
                    type="tool_use",
                ),
            ],
            model="claude-3-opus-20240229",
            role="assistant",
            stop_reason="tool_use",
            stop_sequence=None,
            type="message",
            usage=Usage(input_tokens=1720, output_tokens=194),
        ),
        ai_model_id="claude-3-opus-20240229",
        metadata={},
        content_type="message",
        role=AuthorRole.ASSISTANT,
        name=None,
        items=[
            FunctionCallContent(
                inner_content=None,
                ai_model_id=None,
                metadata={},
                content_type=ContentTypes.FUNCTION_CALL_CONTENT,
                id="test_function_call_content",
                index=1,
                name="math-Add",
                function_name="Add",
                plugin_name="math",
                arguments={"input": 3, "amount": 3},
            ),
            TextContent(
                inner_content=None,
                ai_model_id=None,
                metadata={},
                content_type="text",
                text="<thinking></thinking>",
                encoding=None,
            ),
        ],
        encoding=None,
        finish_reason=FinishReason.TOOL_CALLS,
    )


@pytest.fixture
def mock_streaming_tool_calls_message() -> list:
    stream_events = [
        RawMessageStartEvent(
            message=Message(
                id="test_message_id",
                content=[],
                model="claude-3-opus-20240229",
                role="assistant",
                stop_reason=None,
                stop_sequence=None,
                type="message",
                usage=Usage(input_tokens=1720, output_tokens=2),
            ),
            type="message_start",
        ),
        RawContentBlockStartEvent(content_block=TextBlock(text="", type="text"), index=0, type="content_block_start"),
        RawContentBlockDeltaEvent(
            delta=TextDelta(text="<thinking>", type="text_delta"), index=0, type="content_block_delta"
        ),
        TextEvent(type="text", text="<thinking>", snapshot="<thinking>"),
        RawContentBlockDeltaEvent(
            delta=TextDelta(text="</thinking>", type="text_delta"), index=0, type="content_block_delta"
        ),
        TextEvent(type="text", text="</thinking>", snapshot="<thinking></thinking>"),
        ContentBlockStopEvent(
            index=0, type="content_block_stop", content_block=TextBlock(text="<thinking></thinking>", type="text")
        ),
        RawContentBlockStartEvent(
            content_block=ToolUseBlock(id="test_tool_use_message_id", input={}, name="math-Add", type="tool_use"),
            index=1,
            type="content_block_start",
        ),
        RawContentBlockDeltaEvent(
            delta=InputJSONDelta(partial_json='{"input": 3, "amount": 3}', type="input_json_delta"),
            index=1,
            type="content_block_delta",
        ),
        InputJsonEvent(type="input_json", partial_json='{"input": 3, "amount": 3}', snapshot={"input": 3, "amount": 3}),
        ContentBlockStopEvent(
            index=1,
            type="content_block_stop",
            content_block=ToolUseBlock(
                id="test_tool_use_block_id", input={"input": 3, "amount": 3}, name="math-Add", type="tool_use"
            ),
        ),
        RawMessageDeltaEvent(
            delta=Delta(stop_reason="tool_use", stop_sequence=None),
            type="message_delta",
            usage=MessageDeltaUsage(output_tokens=159),
        ),
        MessageStopEvent(
            type="message_stop",
            message=Message(
                id="test_message_id",
                content=[
                    TextBlock(text="<thinking></thinking>", type="text"),
                    ToolUseBlock(
                        id="test_tool_use_block_id", input={"input": 3, "amount": 3}, name="math-Add", type="tool_use"
                    ),
                ],
                model="claude-3-opus-20240229",
                role="assistant",
                stop_reason="tool_use",
                stop_sequence=None,
                type="message",
                usage=Usage(input_tokens=100, output_tokens=100),
            ),
        ),
    ]

    async def async_generator():
        for event in stream_events:
            yield event

    stream_mock = AsyncMock()
    stream_mock.__aenter__.return_value = async_generator()

    return stream_mock


@pytest.fixture
def mock_tool_call_result_message() -> ChatMessageContent:
    return ChatMessageContent(
        inner_content=None,
        ai_model_id=None,
        metadata={},
        content_type="message",
        role=AuthorRole.TOOL,
        name=None,
        items=[
            FunctionResultContent(
                id="tool_01",
                inner_content=FunctionResult(
                    function=KernelFunctionMetadata(
                        name="Add",
                        plugin_name="math",
                        description="Returns the Addition result of the values provided.",
                        parameters=[
                            KernelParameterMetadata(
                                name="input",
                                description="the first number to add",
                                default_value=None,
                                type_="int",
                                is_required=True,
                                type_object=int,
                                schema_data={"type": "integer", "description": "the first number to add"},
                                function_schema_include=True,
                            ),
                            KernelParameterMetadata(
                                name="amount",
                                description="the second number to add",
                                default_value=None,
                                type_="int",
                                is_required=True,
                                type_object=int,
                                schema_data={"type": "integer", "description": "the second number to add"},
                                function_schema_include=True,
                            ),
                        ],
                        is_prompt=False,
                        is_asynchronous=False,
                        return_parameter=KernelParameterMetadata(
                            name="return",
                            description="the output is a number",
                            default_value=None,
                            type_="int",
                            is_required=True,
                            type_object=int,
                            schema_data={"type": "integer", "description": "the output is a number"},
                            function_schema_include=True,
                        ),
                        additional_properties={},
                    ),
                    value=6,
                    metadata={},
                ),
                value=6,
            )
        ],
        encoding=None,
        finish_reason=FinishReason.TOOL_CALLS,
    )


# mock StreamingChatMessageContent
@pytest.fixture
def mock_streaming_chat_message_content() -> StreamingChatMessageContent:
    return StreamingChatMessageContent(
        choice_index=0,
        inner_content=[
            RawContentBlockDeltaEvent(
                delta=TextDelta(text="<thinking>", type="text_delta"), index=0, type="content_block_delta"
            ),
            RawContentBlockDeltaEvent(
                delta=TextDelta(text="</thinking>", type="text_delta"), index=0, type="content_block_delta"
            ),
            ContentBlockStopEvent(
                index=1,
                type="content_block_stop",
                content_block=ToolUseBlock(
                    id="tool_id",
                    input={"input": 3, "amount": 3},
                    name="math-Add",
                    type="tool_use",
                ),
            ),
            RawMessageDeltaEvent(
                delta=Delta(stop_reason="tool_use", stop_sequence=None),
                type="message_delta",
                usage=MessageDeltaUsage(output_tokens=175),
            ),
        ],
        ai_model_id="claude-3-opus-20240229",
        metadata={},
        role=AuthorRole.ASSISTANT,
        name=None,
        items=[
            StreamingTextContent(
                inner_content=None,
                ai_model_id=None,
                metadata={},
                content_type="text",
                text="<thinking></thinking>",
                encoding=None,
                choice_index=0,
            ),
            FunctionCallContent(
                inner_content=None,
                ai_model_id=None,
                metadata={},
                content_type=ContentTypes.FUNCTION_CALL_CONTENT,
                id="tool_id",
                index=0,
                name="math-Add",
                function_name="Add",
                plugin_name="math",
                arguments='{"input": 3, "amount": 3}',
            ),
        ],
        encoding=None,
        finish_reason=FinishReason.TOOL_CALLS,
    )


@pytest.fixture
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
def mock_settings() -> AnthropicChatPromptExecutionSettings:
    return AnthropicChatPromptExecutionSettings()


@pytest.fixture
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
def mock_anthropic_client_completion() -> AsyncAnthropic:
    client = MagicMock(spec=AsyncAnthropic)

    chat_completion_response = AsyncMock()
    chat_completion_response.content = [TextBlock(text="Hello! It's nice to meet you.", type="text")]
    chat_completion_response.id = "test_id"
    chat_completion_response.model = "claude-3-opus-20240229"
    chat_completion_response.role = "assistant"
    chat_completion_response.stop_reason = "end_turn"
    chat_completion_response.stop_sequence = None
    chat_completion_response.type = "message"
    chat_completion_response.usage = Usage(input_tokens=114, output_tokens=75)

    # Create a MagicMock for the messages attribute
    messages_mock = MagicMock()
    messages_mock.create = AsyncMock(return_value=chat_completion_response)

    # Assign the messages_mock to the client.messages attribute
    client.messages = messages_mock

    return client


@pytest.fixture
def mock_anthropic_client_completion_stream() -> AsyncAnthropic:
    client = MagicMock(spec=AsyncAnthropic)

    # Create MagicMock instances for each event with the spec set to the appropriate class
    mock_raw_message_start_event = MagicMock(spec=RawMessageStartEvent)
    mock_raw_message_start_event.message = MagicMock(spec=Message)
    mock_raw_message_start_event.message.id = "test_message_id"
    mock_raw_message_start_event.message.content = []
    mock_raw_message_start_event.message.model = "claude-3-opus-20240229"
    mock_raw_message_start_event.message.role = "assistant"
    mock_raw_message_start_event.message.stop_reason = None
    mock_raw_message_start_event.message.stop_sequence = None
    mock_raw_message_start_event.message.type = "message"
    mock_raw_message_start_event.message.usage = MagicMock(spec=Usage)
    mock_raw_message_start_event.message.usage.input_tokens = 41
    mock_raw_message_start_event.message.usage.output_tokens = 3
    mock_raw_message_start_event.type = "message_start"

    mock_raw_content_block_start_event = MagicMock(spec=RawContentBlockStartEvent)
    mock_raw_content_block_start_event.content_block = MagicMock(spec=TextBlock)
    mock_raw_content_block_start_event.content_block.text = ""
    mock_raw_content_block_start_event.content_block.type = "text"
    mock_raw_content_block_start_event.index = 0
    mock_raw_content_block_start_event.type = "content_block_start"

    mock_raw_content_block_delta_event = MagicMock(spec=RawContentBlockDeltaEvent)
    mock_raw_content_block_delta_event.delta = MagicMock(spec=TextDelta)
    mock_raw_content_block_delta_event.delta.text = "Hello! It"
    mock_raw_content_block_delta_event.delta.type = "text_delta"
    mock_raw_content_block_delta_event.index = 0
    mock_raw_content_block_delta_event.type = "content_block_delta"

    mock_text_event = MagicMock(spec=TextEvent)
    mock_text_event.type = "text"
    mock_text_event.text = "Hello! It"
    mock_text_event.snapshot = "Hello! It"

    mock_content_block_stop_event = MagicMock(spec=ContentBlockStopEvent)
    mock_content_block_stop_event.index = 0
    mock_content_block_stop_event.type = "content_block_stop"
    mock_content_block_stop_event.content_block = MagicMock(spec=TextBlock)
    mock_content_block_stop_event.content_block.text = "Hello! It's nice to meet you."
    mock_content_block_stop_event.content_block.type = "text"

    mock_raw_message_delta_event = MagicMock(spec=RawMessageDeltaEvent)
    mock_raw_message_delta_event.delta = MagicMock(spec=Delta)
    mock_raw_message_delta_event.delta.stop_reason = "end_turn"
    mock_raw_message_delta_event.delta.stop_sequence = None
    mock_raw_message_delta_event.type = "message_delta"
    mock_raw_message_delta_event.usage = MagicMock(spec=MessageDeltaUsage)
    mock_raw_message_delta_event.usage.output_tokens = 84

    mock_message_stop_event = MagicMock(spec=MessageStopEvent)
    mock_message_stop_event.type = "message_stop"
    mock_message_stop_event.message = MagicMock(spec=Message)
    mock_message_stop_event.message.id = "test_message_stop_id"
    mock_message_stop_event.message.content = [MagicMock(spec=TextBlock)]
    mock_message_stop_event.message.content[0].text = "Hello! It's nice to meet you."
    mock_message_stop_event.message.content[0].type = "text"
    mock_message_stop_event.message.model = "claude-3-opus-20240229"
    mock_message_stop_event.message.role = "assistant"
    mock_message_stop_event.message.stop_reason = "end_turn"
    mock_message_stop_event.message.stop_sequence = None
    mock_message_stop_event.message.type = "message"
    mock_message_stop_event.message.usage = MagicMock(spec=Usage)
    mock_message_stop_event.message.usage.input_tokens = 41
    mock_message_stop_event.message.usage.output_tokens = 84

    # Combine all mock events into a list
    stream_events = [
        mock_raw_message_start_event,
        mock_raw_content_block_start_event,
        mock_raw_content_block_delta_event,
        mock_text_event,
        mock_content_block_stop_event,
        mock_raw_message_delta_event,
        mock_message_stop_event,
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
def mock_chat_message_response() -> Message:
    return Message(
        id="test_message_id",
        content=[TextBlock(text="Hello, how are you?", type="text")],
        model="claude-3-opus-20240229",
        role="assistant",
        stop_reason="end_turn",
        stop_sequence=None,
        type="message",
        usage=Usage(input_tokens=10, output_tokens=10),
    )


@pytest.fixture
def mock_streaming_message_response() -> AsyncGenerator:
    raw_message_start_event = RawMessageStartEvent(
        message=Message(
            id="test_message_id",
            content=[],
            model="claude-3-opus-20240229",
            role="assistant",
            stop_reason=None,
            stop_sequence=None,
            type="message",
            usage=Usage(input_tokens=41, output_tokens=3),
        ),
        type="message_start",
    )

    raw_content_block_start_event = RawContentBlockStartEvent(
        content_block=TextBlock(text="", type="text"),
        index=0,
        type="content_block_start",
    )

    raw_content_block_delta_event = RawContentBlockDeltaEvent(
        delta=TextDelta(text="Hello! It", type="text_delta"),
        index=0,
        type="content_block_delta",
    )

    text_event = TextEvent(
        type="text",
        text="Hello! It",
        snapshot="Hello! It",
    )

    content_block_stop_event = ContentBlockStopEvent(
        index=0,
        type="content_block_stop",
        content_block=TextBlock(text="Hello! It's nice to meet you.", type="text"),
    )

    raw_message_delta_event = RawMessageDeltaEvent(
        delta=Delta(stop_reason="end_turn", stop_sequence=None),
        type="message_delta",
        usage=MessageDeltaUsage(output_tokens=84),
    )

    message_stop_event = MessageStopEvent(
        type="message_stop",
        message=Message(
            id="test_message_stop_id",
            content=[TextBlock(text="Hello! It's nice to meet you.", type="text")],
            model="claude-3-opus-20240229",
            role="assistant",
            stop_reason="end_turn",
            stop_sequence=None,
            type="message",
            usage=Usage(input_tokens=41, output_tokens=84),
        ),
    )

    # Combine all mock events into a list
    stream_events = [
        raw_message_start_event,
        raw_content_block_start_event,
        raw_content_block_delta_event,
        text_event,
        content_block_stop_event,
        raw_message_delta_event,
        message_stop_event,
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    ]

    async def async_generator():
        for event in stream_events:
            yield event

    # Create an AsyncMock for the stream
    stream_mock = AsyncMock()
    stream_mock.__aenter__.return_value = async_generator()

<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    messages_mock = MagicMock()
    messages_mock.stream.return_value = stream_mock

    client.messages = messages_mock

<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    return stream_mock


@pytest.fixture
def mock_anthropic_client_completion(mock_chat_message_response: Message) -> AsyncAnthropic:
    client = MagicMock(spec=AsyncAnthropic)
    messages_mock = MagicMock()
    messages_mock.create = AsyncMock(return_value=mock_chat_message_response)
    client.messages = messages_mock
    return client


@pytest.fixture
def mock_anthropic_client_completion_stream(mock_streaming_message_response: AsyncGenerator) -> AsyncAnthropic:
    client = MagicMock(spec=AsyncAnthropic)
    messages_mock = MagicMock()
    messages_mock.stream.return_value = mock_streaming_message_response
    client.messages = messages_mock
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    return client


@pytest.mark.asyncio
async def test_complete_chat_contents(
    kernel: Kernel,
    mock_settings: AnthropicChatPromptExecutionSettings,
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    mock_anthropic_client_completion: AsyncAnthropic,
):
    chat_history = ChatHistory()
    chat_history.add_user_message("test_user_message")
    chat_history.add_assistant_message("test_assistant_message")

    arguments = KernelArguments()
    chat_completion_base = AnthropicChatCompletion(
        ai_model_id="test_model_id", service_id="test", api_key="", async_client=mock_anthropic_client_completion
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
=======
=======
<<<<<<< div
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    mock_chat_message_response: Message,
):
    client = MagicMock(spec=AsyncAnthropic)
    messages_mock = MagicMock()
    messages_mock.create = AsyncMock(return_value=mock_chat_message_response)
    client.messages = messages_mock

    chat_history = ChatHistory()
    chat_history.add_user_message("test_user_message")

    arguments = KernelArguments()
    chat_completion_base = AnthropicChatCompletion(
        ai_model_id="test_model_id", service_id="test", api_key="", async_client=client
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    )

    content: list[ChatMessageContent] = await chat_completion_base.get_chat_message_contents(
        chat_history=chat_history, settings=mock_settings, kernel=kernel, arguments=arguments
    )

<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    assert content is not None


@pytest.mark.asyncio
async def test_complete_chat_stream_contents(
    kernel: Kernel,
    mock_settings: AnthropicChatPromptExecutionSettings,
    mock_anthropic_client_completion_stream: AsyncAnthropic,
):
    chat_history = MagicMock()
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    assert len(content) > 0
    assert content[0].content != ""
    assert content[0].role == AuthorRole.ASSISTANT


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
    ],
)
@pytest.mark.asyncio
async def test_complete_chat_contents_function_call_behavior_tool_call(
    kernel: Kernel,
    mock_settings: AnthropicChatPromptExecutionSettings,
    function_choice_behavior: FunctionChoiceBehavior,
    model_responses,
    expected_result,
):
    kernel.add_function("test", kernel_function(lambda key: "test", name="test"))
    mock_settings.function_choice_behavior = function_choice_behavior

    arguments = KernelArguments()
    chat_completion_base = AnthropicChatCompletion(ai_model_id="test_model_id", service_id="test", api_key="")

    with (
        patch.object(chat_completion_base, "_inner_get_chat_message_contents", side_effect=model_responses),
    ):
        response: list[ChatMessageContent] = await chat_completion_base.get_chat_message_contents(
            chat_history=ChatHistory(system_message="Test"), settings=mock_settings, kernel=kernel, arguments=arguments
        )

        assert all(isinstance(content, expected_result) for content in response[0].items)


@pytest.mark.asyncio
async def test_complete_chat_contents_function_call_behavior_without_kernel(
    mock_settings: AnthropicChatPromptExecutionSettings,
    mock_anthropic_client_completion: AsyncAnthropic,
):
    chat_history = MagicMock()
    chat_completion_base = AnthropicChatCompletion(
        ai_model_id="test_model_id", service_id="test", api_key="", async_client=mock_anthropic_client_completion
    )

    mock_settings.function_choice_behavior = FunctionChoiceBehavior.Auto()

    with pytest.raises(ServiceInvalidExecutionSettingsError):
        await chat_completion_base.get_chat_message_contents(chat_history=chat_history, settings=mock_settings)


@pytest.mark.asyncio
async def test_complete_chat_stream_contents(
    kernel: Kernel,
    mock_settings: AnthropicChatPromptExecutionSettings,
    mock_streaming_message_response,
):
    client = MagicMock(spec=AsyncAnthropic)
    messages_mock = MagicMock()
    messages_mock.stream.return_value = mock_streaming_message_response
    client.messages = messages_mock

    chat_history = ChatHistory()
    chat_history.add_user_message("test_user_message")

<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    arguments = KernelArguments()

    chat_completion_base = AnthropicChatCompletion(
        ai_model_id="test_model_id",
        service_id="test",
        api_key="",
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        async_client=mock_anthropic_client_completion_stream,
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
        async_client=mock_anthropic_client_completion_stream,
=======
        async_client=client,
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        async_client=client,
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< div
=======
        async_client=client,
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
    )

    async for content in chat_completion_base.get_streaming_chat_message_contents(
        chat_history, mock_settings, kernel=kernel, arguments=arguments
    ):
        assert content is not None


<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
@pytest.mark.asyncio
async def test_anthropic_sdk_exception(kernel: Kernel, mock_settings: AnthropicChatPromptExecutionSettings):
    chat_history = MagicMock()
    arguments = KernelArguments()
    client = MagicMock(spec=AsyncAnthropic)

    # Create a MagicMock for the messages attribute
    messages_mock = MagicMock()
    messages_mock.create.side_effect = Exception("Test Exception")

    # Assign the messages_mock to the client.messages attribute
    client.messages = messages_mock

<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
=======
=======
<<<<<<< div
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
>>>>>>> head
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
    mock_settings: AnthropicChatPromptExecutionSettings,
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
    chat_completion_base = AnthropicChatCompletion(ai_model_id="test_model_id", service_id="test", api_key="")

    with patch.object(chat_completion_base, "_inner_get_streaming_chat_message_contents", side_effect=generator_mocks):
        messages = []
        async for chunk in chat_completion_base.get_streaming_chat_message_contents(
            chat_history=ChatHistory(system_message="Test"), settings=mock_settings, kernel=kernel, arguments=arguments
        ):
            messages.append(chunk)

        response = messages[-1]
        assert all(isinstance(content, expected_result) for content in response[0].items)


@pytest.mark.asyncio
async def test_anthropic_sdk_exception(kernel: Kernel, mock_settings: AnthropicChatPromptExecutionSettings):
    client = MagicMock(spec=AsyncAnthropic)
    messages_mock = MagicMock()
    messages_mock.create.side_effect = Exception("Test Exception")
    client.messages = messages_mock

    chat_history = MagicMock()
    arguments = KernelArguments()

<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    chat_completion_base = AnthropicChatCompletion(
        ai_model_id="test_model_id", service_id="test", api_key="", async_client=client
    )

    with pytest.raises(ServiceResponseException):
        await chat_completion_base.get_chat_message_contents(
            chat_history=chat_history, settings=mock_settings, kernel=kernel, arguments=arguments
        )


@pytest.mark.asyncio
async def test_anthropic_sdk_exception_streaming(kernel: Kernel, mock_settings: AnthropicChatPromptExecutionSettings):
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    chat_history = MagicMock()
    arguments = KernelArguments()
    client = MagicMock(spec=AsyncAnthropic)

    # Create a MagicMock for the messages attribute
    messages_mock = MagicMock()
    messages_mock.stream.side_effect = Exception("Test Exception")

    client.messages = messages_mock

<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> Stashed changes
>>>>>>> head
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
    client = MagicMock(spec=AsyncAnthropic)
    messages_mock = MagicMock()
    messages_mock.stream.side_effect = Exception("Test Exception")
    client.messages = messages_mock

    chat_history = MagicMock()
    arguments = KernelArguments()

<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    chat_completion_base = AnthropicChatCompletion(
        ai_model_id="test_model_id", service_id="test", api_key="", async_client=client
    )

    with pytest.raises(ServiceResponseException):
        async for content in chat_completion_base.get_streaming_chat_message_contents(
            chat_history, mock_settings, kernel=kernel, arguments=arguments
        ):
            assert content is not None


def test_anthropic_chat_completion_init(anthropic_unit_test_env) -> None:
    # Test successful initialization
    anthropic_chat_completion = AnthropicChatCompletion()

    assert anthropic_chat_completion.ai_model_id == anthropic_unit_test_env["ANTHROPIC_CHAT_MODEL_ID"]
    assert isinstance(anthropic_chat_completion, ChatCompletionClientBase)


@pytest.mark.parametrize("exclude_list", [["ANTHROPIC_API_KEY"]], indirect=True)
def test_anthropic_chat_completion_init_with_empty_api_key(anthropic_unit_test_env) -> None:
    ai_model_id = "test_model_id"

    with pytest.raises(ServiceInitializationError):
        AnthropicChatCompletion(
            ai_model_id=ai_model_id,
            env_file_path="test.env",
        )


@pytest.mark.parametrize("exclude_list", [["ANTHROPIC_CHAT_MODEL_ID"]], indirect=True)
def test_anthropic_chat_completion_init_with_empty_model_id(anthropic_unit_test_env) -> None:
    with pytest.raises(ServiceInitializationError):
        AnthropicChatCompletion(
            env_file_path="test.env",
        )


def test_prompt_execution_settings_class(anthropic_unit_test_env):
    anthropic_chat_completion = AnthropicChatCompletion()
    prompt_execution_settings = anthropic_chat_completion.get_prompt_execution_settings_class()
    assert prompt_execution_settings == AnthropicChatPromptExecutionSettings


@pytest.mark.asyncio
async def test_with_different_execution_settings(kernel: Kernel, mock_anthropic_client_completion: MagicMock):
    chat_history = MagicMock()
    settings = OpenAIChatPromptExecutionSettings(temperature=0.2)
    arguments = KernelArguments()
    chat_completion_base = AnthropicChatCompletion(
        ai_model_id="test_model_id", service_id="test", api_key="", async_client=mock_anthropic_client_completion
    )

    await chat_completion_base.get_chat_message_contents(
        chat_history=chat_history, settings=settings, kernel=kernel, arguments=arguments
    )

    assert mock_anthropic_client_completion.messages.create.call_args.kwargs["temperature"] == 0.2


@pytest.mark.asyncio
async def test_with_different_execution_settings_stream(
    kernel: Kernel, mock_anthropic_client_completion_stream: MagicMock
):
    chat_history = MagicMock()
    settings = OpenAIChatPromptExecutionSettings(temperature=0.2, seed=2)
    arguments = KernelArguments()
    chat_completion_base = AnthropicChatCompletion(
        ai_model_id="test_model_id",
        service_id="test",
        api_key="",
        async_client=mock_anthropic_client_completion_stream,
    )

    async for chunk in chat_completion_base.get_streaming_chat_message_contents(
        chat_history, settings, kernel=kernel, arguments=arguments
    ):
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        continue
    assert mock_anthropic_client_completion_stream.messages.stream.call_args.kwargs["temperature"] == 0.2
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        continue
    assert mock_anthropic_client_completion_stream.messages.stream.call_args.kwargs["temperature"] == 0.2
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
        continue
    assert mock_anthropic_client_completion_stream.messages.stream.call_args.kwargs["temperature"] == 0.2
=======
>>>>>>> Stashed changes
=======
        continue
    assert mock_anthropic_client_completion_stream.messages.stream.call_args.kwargs["temperature"] == 0.2
=======
>>>>>>> Stashed changes
>>>>>>> head
        assert chunk is not None
    assert mock_anthropic_client_completion_stream.messages.stream.call_args.kwargs["temperature"] == 0.2


@pytest.mark.asyncio
async def test_prepare_chat_history_for_request_with_system_message(mock_anthropic_client_completion_stream: MagicMock):
    chat_history = ChatHistory()
    chat_history.add_system_message("System message")
    chat_history.add_user_message("User message")
    chat_history.add_assistant_message("Assistant message")
    chat_history.add_system_message("Another system message")

    chat_completion_base = AnthropicChatCompletion(
        ai_model_id="test_model_id",
        service_id="test",
        api_key="",
        async_client=mock_anthropic_client_completion_stream,
    )

    remaining_messages, system_message_content = chat_completion_base._prepare_chat_history_for_request(
        chat_history, role_key="role", content_key="content"
    )

    assert system_message_content == "System message"
    assert remaining_messages == [
        {"role": AuthorRole.USER, "content": "User message"},
        {"role": AuthorRole.ASSISTANT, "content": "Assistant message"},
    ]
    assert not any(msg["role"] == AuthorRole.SYSTEM for msg in remaining_messages)


@pytest.mark.asyncio
async def test_prepare_chat_history_for_request_with_tool_message(
    mock_anthropic_client_completion_stream: MagicMock,
    mock_tool_calls_message: ChatMessageContent,
    mock_tool_call_result_message: ChatMessageContent,
):
    chat_history = ChatHistory()
    chat_history.add_user_message("What is 3+3?")
    chat_history.add_message(mock_tool_calls_message)
    chat_history.add_message(mock_tool_call_result_message)

    chat_completion_client = AnthropicChatCompletion(
        ai_model_id="test_model_id",
        service_id="test",
        api_key="",
        async_client=mock_anthropic_client_completion_stream,
    )

    remaining_messages, system_message_content = chat_completion_client._prepare_chat_history_for_request(
        chat_history, role_key="role", content_key="content"
    )

    assert system_message_content is None
    assert len(remaining_messages) == 3


@pytest.mark.asyncio
async def test_prepare_chat_history_for_request_with_tool_message_streaming(
    mock_anthropic_client_completion_stream: MagicMock,
    mock_streaming_chat_message_content: StreamingChatMessageContent,
    mock_tool_call_result_message: ChatMessageContent,
):
    chat_history = ChatHistory()
    chat_history.add_user_message("What is 3+3?")
    chat_history.add_message(mock_streaming_chat_message_content)
    chat_history.add_message(mock_tool_call_result_message)

    chat_completion = AnthropicChatCompletion(
        ai_model_id="test_model_id",
        service_id="test",
        api_key="",
        async_client=mock_anthropic_client_completion_stream,
    )

    remaining_messages, system_message_content = chat_completion._prepare_chat_history_for_request(
        chat_history,
        role_key="role",
        content_key="content",
        stream=True,
    )

    assert system_message_content is None
    assert len(remaining_messages) == 3


@pytest.mark.asyncio
async def test_send_chat_stream_request_tool_calls(
    mock_streaming_tool_calls_message: MagicMock,
    mock_streaming_chat_message_content: StreamingChatMessageContent,
):
    chat_history = ChatHistory()
    chat_history.add_user_message("What is 3+3?")
    chat_history.add_message(mock_streaming_chat_message_content)

    settings = AnthropicChatPromptExecutionSettings(
        temperature=0.2,
        max_tokens=100,
        top_p=1.0,
        frequency_penalty=0.0,
        presence_penalty=0.0,
        chat_history=chat_history,
    )

    client = MagicMock(spec=AsyncAnthropic)
    messages_mock = MagicMock()
    messages_mock.stream.return_value = mock_streaming_tool_calls_message
    client.messages = messages_mock

    chat_completion = AnthropicChatCompletion(
        ai_model_id="test_model_id",
        service_id="test",
        api_key="",
        async_client=client,
    )

    response = chat_completion._send_chat_stream_request(settings)
    async for message in response:
        assert message is not None


def test_client_base_url(mock_anthropic_client_completion: MagicMock):
    chat_completion_base = AnthropicChatCompletion(
        ai_model_id="test_model_id", service_id="test", api_key="", async_client=mock_anthropic_client_completion
    )

    assert chat_completion_base.service_url() is not None


def test_chat_completion_reset_settings(
    mock_anthropic_client_completion: MagicMock,
):
    chat_completion = AnthropicChatCompletion(
        ai_model_id="test_model_id", service_id="test", api_key="", async_client=mock_anthropic_client_completion
    )

    settings = AnthropicChatPromptExecutionSettings(tools=[{"name": "test"}], tool_choice={"type": "any"})
    chat_completion._reset_function_choice_settings(settings)

    assert settings.tools is None
    assert settings.tool_choice is None
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
