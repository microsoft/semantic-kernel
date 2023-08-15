from semantic_kernel.models.usage_result import UsageResult


def test_usage_result():
    # Test initialization with default values
    result = UsageResult()
    assert result.prompt_tokens == 0
    assert result.completion_tokens == 0
    assert result.total_tokens == 0

    # Test initialization with custom values
    prompt_tokens = 10
    completion_tokens = 20
    total_tokens = 30
    result = UsageResult(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
    )
    assert result.prompt_tokens == prompt_tokens
    assert result.completion_tokens == completion_tokens
    assert result.total_tokens == total_tokens


def test_usage_result_addition():
    # Test addition of two UsageResult objects
    result1 = UsageResult(prompt_tokens=5, completion_tokens=10, total_tokens=15)
    result2 = UsageResult(prompt_tokens=10, completion_tokens=20, total_tokens=30)
    result3 = result1 + result2
    assert result3.prompt_tokens == result1.prompt_tokens + result2.prompt_tokens
    assert (
        result3.completion_tokens
        == result1.completion_tokens + result2.completion_tokens
    )
    assert result3.total_tokens == result1.total_tokens + result2.total_tokens
