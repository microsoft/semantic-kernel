# Copyright (c) Microsoft. All rights reserved.


from semantic_kernel.connectors.ai.open_ai.contents.function_call import FunctionCall
from semantic_kernel.connectors.ai.open_ai.contents.tool_calls import ToolCall


def test_tool_call(tc: ToolCall):
    assert tc.index == 1
    assert tc.id == "1234"
    assert tc.type == "function"
    assert tc.function is not None


def test_add(tc: ToolCall):
    # Test adding two tool calls
    tc2 = ToolCall(
        index=2, id="5678", function=FunctionCall(name="Test-Function", arguments="""{"input2": "world2"}""", id="5678")
    )
    tc3 = tc + tc2
    assert tc3.index == 1
    assert tc3.id == "1234"
    assert tc3.type == "function"
    assert tc3.function.name == "Test-Function"
    assert tc3.function.arguments == """{"input": "world"}{"input2": "world2"}"""
    assert tc3.function.id == "1234"


def test_add_none(tc: ToolCall):
    # Test adding two tool calls with one being None
    tc2 = None
    tc3 = tc + tc2
    assert tc3.index == 1
    assert tc3.id == "1234"
    assert tc3.type == "function"
    assert tc3.function.name == "Test-Function"
    assert tc3.function.arguments == """{"input": "world"}"""
    assert tc3.function.id == "1234"
