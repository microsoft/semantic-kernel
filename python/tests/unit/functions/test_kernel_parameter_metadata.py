# Copyright (c) Microsoft. All rights reserved.

from typing import Any, Type
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata
from semantic_kernel.schema.kernel_json_schema_builder import KernelJsonSchemaBuilder


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


class MockJsonSchemaBuilder:
    @staticmethod
    def build(parameter_type: Type, description: str | None = None) -> dict[str, Any]:
        return {"type": "mock_object", "description": description}

    @staticmethod
    def build_from_type_name(parameter_type: str, description: str | None = None) -> dict[str, Any]:
        return {"type": f"mock_{parameter_type}", "description": description}


@pytest.fixture
def mock_json_schema_builder():
    with patch.object(KernelJsonSchemaBuilder, "build", MockJsonSchemaBuilder.build), patch.object(
        KernelJsonSchemaBuilder, "build_from_type_name", MockJsonSchemaBuilder.build_from_type_name
    ):
        yield


def test_kernel_parameter_metadata_valid(mock_json_schema_builder):
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
    assert metadata.type_object == str
    assert metadata.schema_data == {"type": "mock_object", "description": "A test parameter"}


def test_kernel_parameter_metadata_invalid_name(mock_json_schema_builder):
    with pytest.raises(ValidationError):
        KernelParameterMetadata(
            name="invalid name!", description="A test parameter", default_value="default", type_="str"
        )


def test_kernel_parameter_metadata_infer_schema_with_type_object(mock_json_schema_builder):
    metadata = KernelParameterMetadata(name="param2", type_object=int, description="An integer parameter")
    assert metadata.schema_data == {"type": "mock_object", "description": "An integer parameter"}


def test_kernel_parameter_metadata_infer_schema_with_type_name(mock_json_schema_builder):
    metadata = KernelParameterMetadata(name="param3", type_="int", default_value=42, description="An integer parameter")
    assert metadata.schema_data == {"type": "mock_int", "description": "An integer parameter (default value: 42)"}


def test_kernel_parameter_metadata_without_schema_data(mock_json_schema_builder):
    metadata = KernelParameterMetadata(name="param4", type_="bool")
    assert metadata.schema_data == {"type": "mock_bool", "description": None}


def test_kernel_parameter_metadata_with_partial_data(mock_json_schema_builder):
    metadata = KernelParameterMetadata(name="param5", type_="float", default_value=3.14)
    assert metadata.schema_data == {"type": "mock_float", "description": "(default value: 3.14)"}
