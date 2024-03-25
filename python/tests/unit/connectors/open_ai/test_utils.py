# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

from typing import Callable

import pytest

from semantic_kernel.connectors.ai.open_ai.utils import get_tool_call_object
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.kernel import Kernel


@pytest.fixture
def decorated_function_all_params() -> Callable:  # type: ignore
    @kernel_function
    def test(arg1: str, arg2: str | None, arg3: list[str], arg4: dict[str, str]) -> str:
        return "test"

    return test


def test_get_tool_call_object(kernel: Kernel, decorated_function_all_params):
    kernel.add_plugin("test", [decorated_function_all_params])
    tools = get_tool_call_object(kernel)
    assert len(tools) == 1
    assert tools[0]["type"] == "function"
    assert tools[0]["function"]["parameters"]["properties"]["arg1"]["type"] == "string"
    assert tools[0]["function"]["parameters"]["properties"]["arg2"]["type"] == "string"
    assert tools[0]["function"]["parameters"]["properties"]["arg3"]["type"] == "array"
    assert tools[0]["function"]["parameters"]["properties"]["arg3"]["items"]["type"] == "string"
    assert tools[0]["function"]["parameters"]["properties"]["arg4"]["type"] == "object"
