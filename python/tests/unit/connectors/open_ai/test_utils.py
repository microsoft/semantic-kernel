# Copyright (c) Microsoft. All rights reserved.
from typing import Callable, Dict, List, Optional

import pytest

from semantic_kernel.connectors.ai.open_ai.utils import get_tool_call_object
from semantic_kernel.functions.kernel_function_decorator import kernel_function
from semantic_kernel.kernel import Kernel


@pytest.fixture
def decorated_function_all_params() -> Callable:  # type: ignore
    @kernel_function(name="test")
    def decorated_function_all_params(arg1: str, arg2: Optional[str], arg3: List[str], arg4: Dict[str, str]) -> str:
        return "test"

    return decorated_function_all_params


@pytest.fixture
def decorated_function_all_params2() -> Callable:  # type: ignore
    @kernel_function
    def decorated_function_all_params(arg1: str, arg2: Optional[str], arg3: List[str], arg4: Dict[str, str]) -> str:
        return "test"

    return decorated_function_all_params


def test_get_tool_call_object(kernel: Kernel, decorated_function_all_params, decorated_function_all_params2):
    kernel.add_plugin("test", [decorated_function_all_params])
    tools = get_tool_call_object(kernel)
    assert len(tools) == 1
    assert tools[0]["type"] == "function"
    assert tools[0]["function"]["parameters"]["properties"]["arg1"]["type"] == "string"
    assert tools[0]["function"]["parameters"]["properties"]["arg2"]["type"] == "string"
    assert tools[0]["function"]["parameters"]["properties"]["arg3"]["type"] == "array"
    assert tools[0]["function"]["parameters"]["properties"]["arg3"]["items"]["type"] == "string"
    assert tools[0]["function"]["parameters"]["properties"]["arg4"]["type"] == "object"
