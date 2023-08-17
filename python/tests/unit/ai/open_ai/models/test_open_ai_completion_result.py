from openai.util import convert_to_openai_object

from semantic_kernel.connectors.ai.open_ai.models.open_ai_completion_result import (
    OpenAICompletionResult,
)
from semantic_kernel.models.completion_content import CompletionContent
from semantic_kernel.models.completion_result import CompletionResult
from semantic_kernel.models.finish_reason import FinishReason
from semantic_kernel.models.usage_result import UsageResult


def test_from_openai_object():
    # Create a mock OpenAIObject to use as input
    openai_object = convert_to_openai_object(
        resp={
            "id": "test_id",
            "object": "text_completion",
            "created": 1234567890,
            "model": "test_model",
            "choices": [
                {
                    "index": 0,
                    "finish_reason": "stop",
                    "text": "user input",
                    "logprobs": None,
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
        }
    )

    # Call the method being tested
    result = OpenAICompletionResult.from_openai_object(openai_object, False)

    # Check that the output is of the correct type
    assert isinstance(result, CompletionResult)

    # Check that the output has the correct values
    assert result.id == "test_id"
    assert result.object_type == "text_completion"
    assert result.created == 1234567890
    assert result.model == "test_model"
    assert len(result.choices) == 1
    assert isinstance(result.choices[0], CompletionContent)
    assert result.choices[0].index == 0
    assert result.choices[0].text == "user input"
    assert result.choices[0].finish_reason == FinishReason.STOP
    assert isinstance(result.usage, UsageResult)
    assert result.usage.prompt_tokens == 10
    assert result.usage.completion_tokens == 20
    assert result.usage.total_tokens == 30
