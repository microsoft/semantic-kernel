from pytest import fixture

from semantic_kernel.connectors.ai.open_ai.contents.function_call import FunctionCall
from semantic_kernel.connectors.ai.open_ai.contents.tool_calls import ToolCall


@fixture(scope="module")
def fc():
    return FunctionCall(name="Test-Function", arguments="""{"input": "world"}""", id="1234")


@fixture(scope="module")
def tc(fc: FunctionCall):
    return ToolCall(index=1, id="1234", function=fc)
