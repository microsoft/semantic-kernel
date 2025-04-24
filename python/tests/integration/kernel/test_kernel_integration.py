# Copyright (c) Microsoft. All rights reserved.

import pytest

from semantic_kernel.connectors.ai.open_ai.services.open_ai_chat_completion import OpenAIChatCompletion
from semantic_kernel.kernel import Kernel


def test_kernel_deep_copy_fail_with_services():
    kernel = Kernel()
    kernel.add_service(OpenAIChatCompletion())

    with pytest.raises(TypeError):
        # This will fail because OpenAIChatCompletion is not serializable, more specifically,
        # the client is not serializable
        kernel.model_copy(deep=True)


async def test_kernel_clone():
    kernel = Kernel()
    kernel.add_service(OpenAIChatCompletion())

    kernel_clone = kernel.clone()

    assert kernel_clone is not None
    assert kernel_clone.services is not None and len(kernel_clone.services) > 0

    function_result = await kernel.invoke_prompt("Hello World")
    assert function_result is not None
    assert function_result.value is not None
    assert len(str(function_result)) > 0
