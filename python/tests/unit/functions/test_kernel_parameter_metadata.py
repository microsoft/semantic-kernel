# Copyright (c) Microsoft. All rights reserved.


import pytest
from pydantic import ValidationError

from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata


def test_kernel_parameter_metadata_init():
    metadata = KernelParameterMetadata(
        name="test",
        description="description",
        is_required=True,
        type="str",
        default_value="default",
    )

    assert metadata.name == "test"
    assert metadata.description == "description"
    assert metadata.is_required is True
    assert metadata.default_value == "default"


def test_kernel_parameter_metadata_valid():
    metadata = KernelParameterMetadata(
        name="param1",
        description="A test parameter",
        default_value="default",
        type_="str",
        is_required=True,
        type_object=str,
    )
    assert metadata.name == "param1"
    assert metadata.description == "A test parameter"
    assert metadata.default_value == "default"
    assert metadata.type_ == "str"
    assert metadata.is_required is True
    assert metadata.type_object is str
    assert metadata.schema_data == {"type": "string", "description": "A test parameter"}


def test_kernel_parameter_metadata_invalid_name():
    with pytest.raises(ValidationError):
        KernelParameterMetadata(
            name="invalid name!",
            description="A test parameter",
            default_value="default",
            type_="str",
        )


def test_kernel_parameter_metadata_infer_schema_with_type_object():
    metadata = KernelParameterMetadata(
        name="param2", type_object=int, description="An integer parameter"
    )
    assert metadata.schema_data == {
        "type": "integer",
        "description": "An integer parameter",
    }


def test_kernel_parameter_metadata_infer_schema_with_type_name():
    metadata = KernelParameterMetadata(
        name="param3", type_="int", default_value=42, description="An integer parameter"
    )
    assert metadata.schema_data == {
        "type": "integer",
        "description": "An integer parameter (default value: 42)",
    }


def test_kernel_parameter_metadata_without_schema_data():
    metadata = KernelParameterMetadata(name="param4", type_="bool")
    assert metadata.schema_data == {"type": "boolean"}


def test_kernel_parameter_metadata_with_partial_data():
    metadata = KernelParameterMetadata(name="param5", type_="float", default_value=3.14)
    assert metadata.schema_data == {
        "type": "number",
        "description": "(default value: 3.14)",
    }
