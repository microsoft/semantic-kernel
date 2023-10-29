import pytest

from semantic_kernel.connectors.ai.open_ai.models.chat.function_call import FunctionCall
from semantic_kernel.orchestration.context_variables import ContextVariables


def test_function_call():
    # Test initialization with default values
    fc = FunctionCall(name="Test-Function", arguments="""{"input": "world"}""")
    assert fc.name == "Test-Function"
    assert fc.arguments == """{"input": "world"}"""


@pytest.mark.asyncio
async def test_function_call_to_content_variables(create_kernel):
    # Test parsing arguments to variables
    kernel = create_kernel

    func_call = FunctionCall(
        name="Test-Function",
        arguments="""{"input": "world", "input2": "world2"}""",
    )
    context = kernel.create_new_context()
    assert isinstance(func_call.to_context_variables(), ContextVariables)

    context.variables.merge_or_overwrite(func_call.to_context_variables())
    assert context.variables.input == "world"
    assert context.variables["input2"] == "world2"
