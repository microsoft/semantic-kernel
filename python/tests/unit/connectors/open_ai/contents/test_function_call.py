import pytest

from semantic_kernel.connectors.ai.open_ai.contents.function_call import FunctionCall
from semantic_kernel.exceptions.content_exceptions import (
    FunctionCallInvalidArgumentsException,
    FunctionCallInvalidNameException,
)
from semantic_kernel.functions.kernel_arguments import KernelArguments


def test_function_call(function_call: FunctionCall):
    assert function_call.name == "Test-Function"
    assert function_call.arguments == """{"input": "world"}"""


def test_add(function_call: FunctionCall):
    # Test adding two function calls
    fc2 = FunctionCall(name="Test-Function", arguments="""{"input2": "world2"}""")
    fc3 = function_call + fc2
    assert fc3.name == "Test-Function"
    assert fc3.arguments == """{"input": "world"}{"input2": "world2"}"""


def test_add_none(function_call: FunctionCall):
    # Test adding two function calls with one being None
    fc2 = None
    fc3 = function_call + fc2
    assert fc3.name == "Test-Function"
    assert fc3.arguments == """{"input": "world"}"""


def test_parse_arguments(function_call: FunctionCall):
    # Test parsing arguments to dictionary
    assert function_call.parse_arguments() == {"input": "world"}


def test_parse_arguments_none():
    # Test parsing arguments to dictionary
    fc = FunctionCall(name="Test-Function")
    assert fc.parse_arguments() is None


def test_parse_arguments_fail():
    # Test parsing arguments to dictionary
    fc = FunctionCall(name="Test-Function", arguments="""{"input": "world}""")
    with pytest.raises(FunctionCallInvalidArgumentsException):
        fc.parse_arguments()


def test_to_kernel_arguments(function_call: FunctionCall):
    # Test parsing arguments to variables
    arguments = KernelArguments()
    assert isinstance(function_call.to_kernel_arguments(), KernelArguments)
    arguments.update(function_call.to_kernel_arguments())
    assert arguments["input"] == "world"


def test_to_kernel_arguments_none():
    # Test parsing arguments to variables
    fc = FunctionCall(name="Test-Function")
    assert fc.to_kernel_arguments() == KernelArguments()


def test_split_name(function_call: FunctionCall):
    # Test splitting the name into plugin and function name
    assert function_call.split_name() == ["Test", "Function"]


def test_split_name_name_only():
    # Test splitting the name into plugin and function name
    fc = FunctionCall(name="Function")
    assert fc.split_name() == ["", "Function"]


def test_split_name_dict(function_call: FunctionCall):
    # Test splitting the name into plugin and function name
    assert function_call.split_name_dict() == {"plugin_name": "Test", "function_name": "Function"}


def test_split_name_none():
    fc = FunctionCall(id="1234")
    with pytest.raises(FunctionCallInvalidNameException):
        fc.split_name()


def test_fc_dump(function_call: FunctionCall):
    # Test dumping the function call to dictionary
    dumped = function_call.model_dump()
    assert dumped == {
        "name": "Test-Function",
        "arguments": '{"input": "world"}',
    }


def test_fc_dump_json(function_call: FunctionCall):
    # Test dumping the function call to dictionary
    dumped = function_call.model_dump_json()
    assert dumped == """{"name":"Test-Function","arguments":"{\\"input\\": \\"world\\"}"}"""
