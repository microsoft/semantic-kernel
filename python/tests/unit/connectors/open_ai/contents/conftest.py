from pytest import fixture

from semantic_kernel.connectors.ai.open_ai.contents.function_call import FunctionCall
from semantic_kernel.connectors.ai.open_ai.contents.tool_calls import ToolCall


@fixture(scope="module")
def function_call():
    return FunctionCall(name="Test-Function", arguments='{"input": "world"}')


@fixture(scope="module")
def tool_call(function_call: FunctionCall):
    return ToolCall(id="1234", function=function_call)
