# Copyright (c) Microsoft. All rights reserved.


from semantic_kernel.connectors.ai.open_ai.contents.function_call import FunctionCall
from semantic_kernel.connectors.ai.open_ai.contents.tool_calls import ToolCall


def test_tool_call(tool_call: ToolCall):
    assert tool_call.id == "1234"
    assert tool_call.type == "function"
    assert tool_call.function is not None


def test_add(tool_call: ToolCall):
    # Test adding two tool calls
    tool_call2 = ToolCall(id="5678", function=FunctionCall(name="Test-Function", arguments="""{"input2": "world2"}"""))
    tool_call3 = tool_call + tool_call2
    assert tool_call3.id == "1234"
    assert tool_call3.type == "function"
    assert tool_call3.function.name == "Test-Function"
    assert tool_call3.function.arguments == """{"input": "world"}{"input2": "world2"}"""


def test_add_none(tool_call: ToolCall):
    # Test adding two tool calls with one being None
    tool_call2 = None
    tool_call3 = tool_call + tool_call2
    assert tool_call3.id == "1234"
    assert tool_call3.type == "function"
    assert tool_call3.function.name == "Test-Function"
    assert tool_call3.function.arguments == """{"input": "world"}"""


def test_dump_json(tool_call: ToolCall):
    assert (
        tool_call.model_dump_json()
        == """{"id":"1234","type":"function","function":{"name":"Test-Function","arguments":"{\\"input\\": \\"world\\"}"}}"""  # noqa: E501
    )
