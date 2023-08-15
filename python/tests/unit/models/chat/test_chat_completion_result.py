import time
from typing import List

from semantic_kernel.models.chat.chat_completion_content import (
    ChatCompletionChunkContent,
)
from semantic_kernel.models.chat.chat_completion_result import ChatCompletionResult
from semantic_kernel.models.chat.chat_message import ChatMessage
from semantic_kernel.models.completion_result_base import CompletionResultBase
from semantic_kernel.models.finish_reason import FinishReasonEnum


def test_from_chunk_list():
    messages = [
        ChatMessage(
            role="user",
            fixed_content="How ",
        ),
        ChatMessage(
            role="user",
            fixed_content="are ",
        ),
        ChatMessage(
            role="user",
            fixed_content="you?",
        ),
    ]
    chunk_list: List[CompletionResultBase] = [
        ChatCompletionResult(
            id="123",
            object_type="chat.completion.chunk",
            created=int(time.time()),
            model="test_model",
            choices=[
                ChatCompletionChunkContent(
                    index=0, finish_reason=None, delta=messages[0]
                ),
            ],
            usage=None,
            is_streaming_result=True,
        ),
        ChatCompletionResult(
            id="123",
            object_type="chat.completion.chunk",
            created=int(time.time()),
            model="test_model",
            choices=[
                ChatCompletionChunkContent(
                    index=0, finish_reason=None, delta=messages[1]
                ),
            ],
            usage=None,
            is_streaming_result=True,
        ),
        ChatCompletionResult(
            id="123",
            object_type="chat.completion.chunk",
            created=int(time.time()),
            model="test_model",
            choices=[
                ChatCompletionChunkContent(
                    index=0, finish_reason="stop", delta=messages[2]
                ),
            ],
            usage=None,
            is_streaming_result=True,
        ),
    ]

    result = ChatCompletionResult.from_chunk_list(chunk_list)

    assert result.id == "123"
    assert result.object_type == "chat.completion"
    assert result.created == chunk_list[0].created
    assert result.model == "test_model"
    assert result.usage is None
    assert result.is_streaming_result is False

    assert len(result.choices) == 1

    assert result.choices[0].index == 0
    assert result.choices[0].message.fixed_content == "How are you?"
    assert result.choices[0].finish_reason == FinishReasonEnum.stop
