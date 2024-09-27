# Copyright (c) Microsoft. All rights reserved.

from typing import Any

import pytest

from semantic_kernel.contents.kernel_content import KernelContent
from semantic_kernel.exceptions.function_exceptions import FunctionResultError
from semantic_kernel.functions.function_result import FunctionResult
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata


def test_function_result_str_with_value():
    result = FunctionResult(
        function=KernelFunctionMetadata(
            name="test_function", is_prompt=False, is_asynchronous=False
        ),
        value="test_value",
    )
    assert str(result) == "test_value"


def test_function_result_str_with_list_value():
    result = FunctionResult(
        function=KernelFunctionMetadata(
            name="test_function", is_prompt=False, is_asynchronous=False
        ),
        value=["test_value1", "test_value2"],
    )
    assert str(result) == "test_value1,test_value2"


def test_function_result_str_with_kernel_content_list():
    class MockKernelContent(KernelContent):
        def __str__(self) -> str:
            return "mock_content"

        def to_element(self) -> Any:
            pass

        @classmethod
        def from_element(cls: type["KernelContent"], element: Any) -> "KernelContent":
            pass

        def to_dict(self) -> dict[str, Any]:
            pass

    content = MockKernelContent(inner_content="inner_content")
    result = FunctionResult(
        function=KernelFunctionMetadata(
            name="test_function", is_prompt=False, is_asynchronous=False
        ),
        value=[content],
    )
    assert str(result) == "mock_content"


def test_function_result_str_with_dict_value():
    result = FunctionResult(
        function=KernelFunctionMetadata(
            name="test_function", is_prompt=False, is_asynchronous=False
        ),
        value={"key1": "value1", "key2": "value2"},
    )
    assert str(result) == "value2"


def test_function_result_str_empty_value():
    result = FunctionResult(
        function=KernelFunctionMetadata(
            name="test_function", is_prompt=False, is_asynchronous=False
        ),
        value=None,
    )
    assert str(result) == ""


def test_function_result_str_with_conversion_error():
    class Unconvertible:
        def __str__(self):
            raise ValueError("Cannot convert to string")

    result = FunctionResult(
        function=KernelFunctionMetadata(
            name="test_function", is_prompt=False, is_asynchronous=False
        ),
        value=Unconvertible(),
    )
    with pytest.raises(FunctionResultError, match="Failed to convert value to string"):
        str(result)


def test_function_result_get_inner_content_with_list():
    class MockKernelContent(KernelContent):
        def __str__(self) -> str:
            return "mock_content"

        def to_element(self) -> Any:
            pass

        @classmethod
        def from_element(cls: type["KernelContent"], element: Any) -> "KernelContent":
            pass

        def to_dict(self) -> dict[str, Any]:
            pass

    content = MockKernelContent(inner_content="inner_content")
    result = FunctionResult(
        function=KernelFunctionMetadata(
            name="test_function", is_prompt=False, is_asynchronous=False
        ),
        value=[content],
    )
    assert result.get_inner_content() == "inner_content"


def test_function_result_get_inner_content_with_kernel_content():
    class MockKernelContent(KernelContent):
        def __str__(self) -> str:
            return "mock_content"

        def to_element(self) -> Any:
            pass

        @classmethod
        def from_element(cls: type["KernelContent"], element: Any) -> "KernelContent":
            pass

        def to_dict(self) -> dict[str, Any]:
            pass

    content = MockKernelContent(inner_content="inner_content")
    result = FunctionResult(
        function=KernelFunctionMetadata(
            name="test_function", is_prompt=False, is_asynchronous=False
        ),
        value=content,
    )
    assert result.get_inner_content() == "inner_content"


def test_function_result_get_inner_content_no_inner_content():
    result = FunctionResult(
        function=KernelFunctionMetadata(
            name="test_function", is_prompt=False, is_asynchronous=False
        ),
        value="test_value",
    )
    assert result.get_inner_content() is None
