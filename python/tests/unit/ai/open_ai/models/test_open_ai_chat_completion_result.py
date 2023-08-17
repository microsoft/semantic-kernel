from openai.util import convert_to_openai_object

from semantic_kernel.connectors.ai.open_ai.models.open_ai_chat_completion_result import (
    OpenAIChatCompletionResult,
)
from semantic_kernel.connectors.ai.open_ai.models.open_ai_chat_message import (
    OpenAIChatMessage,
)
from semantic_kernel.models.chat.chat_completion_content import ChatCompletionContent
from semantic_kernel.models.chat.chat_completion_result import ChatCompletionResult
from semantic_kernel.models.finish_reason import FinishReason
from semantic_kernel.models.usage_result import UsageResult


def test_from_openai_object():
    # Create a mock OpenAIObject to use as input
    openai_object = convert_to_openai_object(
        resp={
            "id": "test_id",
            "object": "chat.completion",
            "created": 1234567890,
            "model": "test_model",
            "choices": [
                {
                    "index": 0,
                    "finish_reason": "stop",
                    "message": {"role": "assistant", "content": "user input"},
                    "content_filter_results": {},
                }
            ],
            "usage": {"prompt_tokens": 10, "completion_tokens": 20, "total_tokens": 30},
        }
    )

    # Call the method being tested
    result = OpenAIChatCompletionResult.from_openai_object(openai_object, False)

    # Check that the output is of the correct type
    assert isinstance(result, ChatCompletionResult)

    # Check that the output has the correct values
    assert result.id == "test_id"
    assert result.object_type == "chat.completion"
    assert result.created == 1234567890
    assert result.model == "test_model"
    assert len(result.choices) == 1
    assert isinstance(result.choices[0], ChatCompletionContent)
    assert result.choices[0].index == 0
    assert isinstance(result.choices[0].message, OpenAIChatMessage)
    assert result.choices[0].message.role == "assistant"
    assert result.choices[0].message.content == "user input"
    assert result.choices[0].finish_reason == FinishReason.STOP
    assert isinstance(result.usage, UsageResult)
    assert result.usage.prompt_tokens == 10
    assert result.usage.completion_tokens == 20
    assert result.usage.total_tokens == 30
