from semantic_kernel.models.completion_content import CompletionContent
from semantic_kernel.models.finish_reason import FinishReasonEnum


def test_completion_content():
    # Test initialization with default values
    content = CompletionContent(index=0)
    assert content.index == 0
    assert content.finish_reason is None
    assert content.logprobs is None
    assert content.text is None

    # Test initialization with custom values
    logprobs = {"a": 1, "b": 2}
    text = "test"
    content = CompletionContent(
        index=0, logprobs=logprobs, text=text, finish_reason="stop"
    )
    assert content.logprobs == logprobs
    assert content.text == text
    assert content.finish_reason == FinishReasonEnum.stop
