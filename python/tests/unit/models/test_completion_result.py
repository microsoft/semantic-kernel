import time
from typing import List

from semantic_kernel.models.completion_content import CompletionContent
from semantic_kernel.models.completion_result import CompletionResult
from semantic_kernel.models.completion_result_base import CompletionResultBase
from semantic_kernel.models.finish_reason import FinishReasonEnum


def test_from_chunk_list():
    chunk_list: List[CompletionResultBase] = [
        CompletionResult(
            id="123",
            object_type="text_completion.chunk",
            created=int(time.time()),
            model="test_model",
            choices=[
                CompletionContent(index=0, text="How ", finish_reason=None),
            ],
            usage=None,
            is_streaming_result=True,
        ),
        CompletionResult(
            id="123",
            object_type="text_completion.chunk",
            created=int(time.time()),
            model="test_model",
            choices=[
                CompletionContent(index=0, text="are ", finish_reason=None),
            ],
            usage=None,
            is_streaming_result=True,
        ),
        CompletionResult(
            id="123",
            object_type="text_completion.chunk",
            created=int(time.time()),
            model="test_model",
            choices=[
                CompletionContent(index=0, text="you?", finish_reason="stop"),
            ],
            usage=None,
            is_streaming_result=True,
        ),
    ]

    result = CompletionResult.from_chunk_list(chunk_list)

    assert result.id == "123"
    assert result.object_type == "text_completion"
    assert result.created == chunk_list[0].created
    assert result.model == "test_model"
    assert result.usage is None
    assert result.is_streaming_result is False

    assert len(result.choices) == 1

    assert result.choices[0].index == 0
    assert result.choices[0].text == "How are you?"
    assert result.choices[0].finish_reason == FinishReasonEnum.stop
