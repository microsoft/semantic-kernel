import pytest

from semantic_kernel.connectors.ai.open_ai.contents.function_call import FunctionCall
from semantic_kernel.exceptions.content_exceptions import (
    FunctionCallInvalidArgumentsException,
    FunctionCallInvalidNameException,
)
from semantic_kernel.functions.kernel_arguments import KernelArguments


def test_function_call(fc: FunctionCall):
    assert fc.name == "Test-Function"
    assert fc.arguments == """{"input": "world"}"""
    assert fc.id == "1234"


def test_add(fc: FunctionCall):
    # Test adding two function calls
    fc2 = FunctionCall(name="Test-Function", arguments="""{"input2": "world2"}""", id="1234")
    fc3 = fc + fc2
    assert fc3.name == "Test-Function"
    assert fc3.arguments == """{"input": "world"}{"input2": "world2"}"""
    assert fc3.id == "1234"


def test_add_none(fc: FunctionCall):
    # Test adding two function calls with one being None
    fc2 = None
    fc3 = fc + fc2
    assert fc3.name == "Test-Function"
    assert fc3.arguments == """{"input": "world"}"""
    assert fc3.id == "1234"


def test_parse_arguments(fc: FunctionCall):
    # Test parsing arguments to dictionary
    assert fc.parse_arguments() == {"input": "world"}


def test_parse_arguments_none():
    # Test parsing arguments to dictionary
    fc = FunctionCall(name="Test-Function", id="1234")
    assert fc.parse_arguments() is None


def test_parse_arguments_fail():
    # Test parsing arguments to dictionary
    fc = FunctionCall(name="Test-Function", arguments="""{"input": "world}""", id="1234")
    with pytest.raises(FunctionCallInvalidArgumentsException):
        fc.parse_arguments()


def test_to_kernel_arguments(fc: FunctionCall):
    # Test parsing arguments to variables
    arguments = KernelArguments()
    assert isinstance(fc.to_kernel_arguments(), KernelArguments)
    arguments.update(fc.to_kernel_arguments())
    assert arguments["input"] == "world"


def test_to_kernel_arguments_none():
    # Test parsing arguments to variables
    fc = FunctionCall(name="Test-Function", id="1234")
    assert fc.to_kernel_arguments() == KernelArguments()


def test_split_name(fc: FunctionCall):
    # Test splitting the name into plugin and function name
    assert fc.split_name() == ["Test", "Function"]


def test_split_name_name_only():
    # Test splitting the name into plugin and function name
    fc = FunctionCall(name="Function", id="1234")
    assert fc.split_name() == ["", "Function"]


def test_split_name_dict(fc: FunctionCall):
    # Test splitting the name into plugin and function name
    assert fc.split_name_dict() == {"plugin_name": "Test", "function_name": "Function"}


def test_split_name_none():
    fc = FunctionCall(id="1234")
    with pytest.raises(FunctionCallInvalidNameException):
        fc.split_name()
