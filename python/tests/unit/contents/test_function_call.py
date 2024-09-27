# Copyright (c) Microsoft. All rights reserved.

import pytest

from semantic_kernel.contents.function_call_content import FunctionCallContent
from semantic_kernel.exceptions.content_exceptions import (
    ContentAdditionException,
    FunctionCallInvalidArgumentsException,
    FunctionCallInvalidNameException,
)
from semantic_kernel.functions.kernel_arguments import KernelArguments


def test_init_from_names():
    # Test initializing function call from names
    fc = FunctionCallContent(
        function_name="Function", plugin_name="Test", arguments="""{"input": "world"}"""
    )
    assert fc.name == "Test-Function"
    assert fc.function_name == "Function"
    assert fc.plugin_name == "Test"
    assert fc.arguments == """{"input": "world"}"""
    assert str(fc) == 'Test-Function({"input": "world"})'


def test_init_dict_args():
    # Test initializing function call with the args already as a dictionary
    fc = FunctionCallContent(
        function_name="Function", plugin_name="Test", arguments={"input": "world"}
    )
    assert fc.name == "Test-Function"
    assert fc.function_name == "Function"
    assert fc.plugin_name == "Test"
    assert fc.arguments == {"input": "world"}
    assert str(fc) == 'Test-Function({"input": "world"})'


def test_init_with_metadata():
    # Test initializing function call from names
    fc = FunctionCallContent(
        function_name="Function", plugin_name="Test", metadata={"test": "test"}
    )
    assert fc.name == "Test-Function"
    assert fc.function_name == "Function"
    assert fc.plugin_name == "Test"
    assert fc.metadata == {"test": "test"}


def test_function_call(function_call: FunctionCallContent):
    assert function_call.name == "Test-Function"
    assert function_call.arguments == """{"input": "world"}"""
    assert function_call.function_name == "Function"
    assert function_call.plugin_name == "Test"


def test_add(function_call: FunctionCallContent):
    # Test adding two function calls
    fc2 = FunctionCallContent(
        id="test", name="Test-Function", arguments="""{"input2": "world2"}"""
    )
    fc3 = function_call + fc2
    assert fc3.name == "Test-Function"
    assert fc3.arguments == """{"input": "world"}{"input2": "world2"}"""


def test_add_empty():
    # Test adding two function calls
    fc1 = FunctionCallContent(id="test1", name="Test-Function", arguments=None)
    fc2 = FunctionCallContent(id="test1", name="Test-Function", arguments="")
    fc3 = fc1 + fc2
    assert fc3.name == "Test-Function"
    assert fc3.arguments == "{}"
    fc1 = FunctionCallContent(
        id="test1", name="Test-Function", arguments="""{"input2": "world2"}"""
    )
    fc2 = FunctionCallContent(id="test1", name="Test-Function", arguments="")
    fc3 = fc1 + fc2
    assert fc3.name == "Test-Function"
    assert fc3.arguments == """{"input2": "world2"}"""
    fc1 = FunctionCallContent(id="test1", name="Test-Function", arguments="{}")
    fc2 = FunctionCallContent(
        id="test1", name="Test-Function", arguments="""{"input2": "world2"}"""
    )
    fc3 = fc1 + fc2
    assert fc3.name == "Test-Function"
    assert fc3.arguments == """{"input2": "world2"}"""


def test_add_none(function_call: FunctionCallContent):
    # Test adding two function calls with one being None
    fc2 = None
    fc3 = function_call + fc2
    assert fc3.name == "Test-Function"
    assert fc3.arguments == """{"input": "world"}"""


def test_add_dict_args():
    # Test adding two function calls
    fc1 = FunctionCallContent(
        id="test1", name="Test-Function", arguments={"input1": "world"}
    )
    fc2 = FunctionCallContent(
        id="test1", name="Test-Function", arguments={"input2": "world2"}
    )
    fc3 = fc1 + fc2
    assert fc3.name == "Test-Function"
    assert fc3.arguments == {"input1": "world", "input2": "world2"}


def test_add_one_dict_args_fail():
    # Test adding two function calls
    fc1 = FunctionCallContent(
        id="test1", name="Test-Function", arguments="""{"input1": "world"}"""
    )
    fc2 = FunctionCallContent(
        id="test1", name="Test-Function", arguments={"input2": "world2"}
    )
    with pytest.raises(ContentAdditionException):
        fc1 + fc2


def test_add_fail_id():
    # Test adding two function calls
    fc1 = FunctionCallContent(
        id="test1", name="Test-Function", arguments="""{"input2": "world2"}"""
    )
    fc2 = FunctionCallContent(
        id="test2", name="Test-Function", arguments="""{"input2": "world2"}"""
    )
    with pytest.raises(ContentAdditionException):
        fc1 + fc2


def test_add_fail_index():
    # Test adding two function calls
    fc1 = FunctionCallContent(
        id="test", index=0, name="Test-Function", arguments="""{"input2": "world2"}"""
    )
    fc2 = FunctionCallContent(
        id="test", index=1, name="Test-Function", arguments="""{"input2": "world2"}"""
    )
    with pytest.raises(ContentAdditionException):
        fc1 + fc2


def test_parse_arguments(function_call: FunctionCallContent):
    # Test parsing arguments to dictionary
    assert function_call.parse_arguments() == {"input": "world"}


def test_parse_arguments_dict():
    # Test parsing arguments to dictionary
    fc = FunctionCallContent(
        id="test", name="Test-Function", arguments={"input": "world"}
    )
    assert fc.parse_arguments() == {"input": "world"}


def test_parse_arguments_none():
    # Test parsing arguments to dictionary
    fc = FunctionCallContent(id="test", name="Test-Function")
    assert fc.parse_arguments() is None


def test_parse_arguments_fail():
    # Test parsing arguments to dictionary
    fc = FunctionCallContent(
        id=None, name="Test-Function", arguments="""{"input": "world}"""
    )
    with pytest.raises(FunctionCallInvalidArgumentsException):
        fc.parse_arguments()


def test_to_kernel_arguments(function_call: FunctionCallContent):
    # Test parsing arguments to variables
    arguments = KernelArguments()
    assert isinstance(function_call.to_kernel_arguments(), KernelArguments)
    arguments.update(function_call.to_kernel_arguments())
    assert arguments["input"] == "world"


def test_to_kernel_arguments_none():
    # Test parsing arguments to variables
    fc = FunctionCallContent(id="test", name="Test-Function")
    assert fc.to_kernel_arguments() == KernelArguments()


def test_split_name(function_call: FunctionCallContent):
    # Test splitting the name into plugin and function name
    assert function_call.split_name() == ["Test", "Function"]


def test_split_name_name_only():
    # Test splitting the name into plugin and function name
    fc = FunctionCallContent(id="test", name="Function")
    assert fc.split_name() == ["", "Function"]


def test_split_name_dict(function_call: FunctionCallContent):
    # Test splitting the name into plugin and function name
    assert function_call.split_name_dict() == {
        "plugin_name": "Test",
        "function_name": "Function",
    }


def test_split_name_none():
    fc = FunctionCallContent(id="1234")
    with pytest.raises(FunctionCallInvalidNameException):
        fc.split_name()


def test_fc_dump(function_call: FunctionCallContent):
    # Test dumping the function call to dictionary
    dumped = function_call.model_dump(exclude_none=True)
    assert dumped == {
        "content_type": "function_call",
        "id": "test",
        "name": "Test-Function",
        "function_name": "Function",
        "plugin_name": "Test",
        "arguments": '{"input": "world"}',
        "metadata": {},
    }


def test_fc_dump_json(function_call: FunctionCallContent):
    # Test dumping the function call to dictionary
    dumped = function_call.model_dump_json(exclude_none=True)
    assert (
        dumped
        == """{"metadata":{},"content_type":"function_call","id":"test","name":"Test-Function","function_name":"Function","plugin_name":"Test","arguments":"{\\"input\\": \\"world\\"}"}"""  # noqa: E501
        == """{"metadata":{},"content_type":"function_call","id":"test","name":"Test-Function","arguments":"{\\"input\\": \\"world\\"}"}"""  # noqa: E501
    )
