# Copyright (c) Microsoft. All rights reserved.


from typing import Any
from unittest.mock import Mock

import pytest

from semantic_kernel.contents.chat_message_content import ChatMessageContent
from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.contents.function_result_content import FunctionResultContent
from semantic_kernel.contents.image_content import ImageContent
from semantic_kernel.contents.text_content import TextContent
from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata


def test_init():
    frc = FunctionResultContent(id="test", name="test-function", result="test-result", metadata={"test": "test"})
    assert frc.name == "test-function"
    assert frc.function_name == "function"
    assert frc.plugin_name == "test"
    assert frc.metadata == {"test": "test"}
    assert frc.result == "test-result"
    assert str(frc) == "test-result"
    assert frc.split_name() == ["test", "function"]
    assert frc.to_dict() == {
        "tool_call_id": "test",
        "content": "test-result",
    }


def test_init_from_names():
    frc = FunctionResultContent(id="test", function_name="Function", plugin_name="Test", result="test-result")
    assert frc.name == "Test-Function"
    assert frc.function_name == "Function"
    assert frc.plugin_name == "Test"
    assert frc.result == "test-result"
    assert str(frc) == "test-result"


@pytest.mark.parametrize(
    "result",
    [
        "Hello world!",
        123,
        {"test": "test"},
        FunctionResult(function=Mock(spec=KernelFunctionMetadata), value="Hello world!"),
        TextContent(text="Hello world!"),
        ChatMessageContent(role="user", content="Hello world!"),
        ChatMessageContent(role="user", items=[ImageContent(uri="https://example.com")]),
        ChatMessageContent(role="user", items=[FunctionResultContent(id="test", name="test", result="Hello world!")]),
    ],
    ids=[
        "str",
        "int",
        "dict",
        "FunctionResult",
        "TextContent",
        "ChatMessageContent",
        "ChatMessageContent-ImageContent",
        "ChatMessageContent-FunctionResultContent",
    ],
)
def test_from_fcc_and_result(result: Any):
    fcc = FunctionCallContent(
        id="test", name="test-function", arguments='{"input": "world"}', metadata={"test": "test"}
    )
    frc = FunctionResultContent.from_function_call_content_and_result(fcc, result, {"test2": "test2"})
    assert frc.name == "test-function"
    assert frc.function_name == "function"
    assert frc.plugin_name == "test"
    assert frc.result is not None
    assert frc.metadata == {"test": "test", "test2": "test2"}


def test_to_cmc():
    frc = FunctionResultContent(id="test", name="test-function", result="test-result")
    cmc = frc.to_chat_message_content()
    assert cmc.role.value == "tool"
    assert cmc.items[0].result == "test-result"


def test_serialize():
    class CustomResultClass:
        def __init__(self, result):
            self.result = result

        def __str__(self) -> str:
            return self.result

    custom_result = CustomResultClass(result="test")
    frc = FunctionResultContent(id="test", name="test-function", result=custom_result)
    assert (
        frc.model_dump_json(exclude_none=True)
        == """{"metadata":{},"content_type":"function_result","id":"test","result":"test","name":"test-function","function_name":"function","plugin_name":"test"}"""  # noqa: E501
    )
