from unittest.mock import AsyncMock, Mock

import pytest
from semantic_kernel import Kernel
from semantic_kernel.connectors.ai.text_completion_client_base import (
    TextCompletionClientBase,
)


def setup_mocks():
    mock_text_completion_client = Mock()
    mock_text_completion_client.complete_async = AsyncMock(
        return_value=["LLM Result about UnitTests"]
    )

    return mock_text_completion_client


@pytest.mark.asyncio
@pytest.mark.parametrize("pipeline_count", [1, 2])
async def test_run_async_handles_pre_invocation(pipeline_count):
    # Arrange
    kernel = Kernel()
    mock_text_completion = setup_mocks()
    kernel.add_text_completion_service("mock_service", mock_text_completion)

    semantic_function = kernel.create_semantic_function(
        "Write a simple phrase about UnitTests"
    )

    invoked = 0

    def invoking_handler(sender, e):
        nonlocal invoked
        invoked += 1

    kernel.add_function_invoking_handler(invoking_handler)
    functions = [semantic_function] * pipeline_count

    # Act
    result = await kernel.run_async(*functions)

    # Assert
    assert invoked == pipeline_count
    mock_text_completion.complete_async.assert_called_once()


if __name__ == "__main__":
    pytest.main(["-s", "-v", __file__])
