# Copyright (c) Microsoft. All rights reserved.


from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.schema.kernel_json_schema_builder import KernelJsonSchemaBuilder


class ExampleModel(KernelBaseModel):
    name: str
    age: int


class AnotherModel:
    title: str
    score: float


def test_build_with_kernel_base_model():
    expected_schema = {"type": "object", "properties": {"name": {"type": "string"}, "age": {"type": "integer"}}}
    result = KernelJsonSchemaBuilder.build(ExampleModel)
    assert result == expected_schema


def test_build_with_model_with_annotations():
    expected_schema = {"type": "object", "properties": {"title": {"type": "string"}, "score": {"type": "number"}}}
    result = KernelJsonSchemaBuilder.build(AnotherModel)
    assert result == expected_schema


def test_build_with_primitive_type():
    expected_schema = {"type": "string"}
    result = KernelJsonSchemaBuilder.build(str)
    assert result == expected_schema

    expected_schema = {"type": "integer"}
    result = KernelJsonSchemaBuilder.build(int)
    assert result == expected_schema


def test_build_with_primitive_type_and_description():
    expected_schema = {"type": "string", "description": "A simple string"}
    result = KernelJsonSchemaBuilder.build(str, description="A simple string")
    assert result == expected_schema


def test_build_model_schema():
    expected_schema = {"type": "object", "properties": {"name": {"type": "string"}, "age": {"type": "integer"}}}
    result = KernelJsonSchemaBuilder.build_model_schema(ExampleModel)
    assert result == expected_schema


def test_build_from_type_name():
    expected_schema = {"type": "string", "description": "A simple string"}
    result = KernelJsonSchemaBuilder.build_from_type_name("str", description="A simple string")
    assert result == expected_schema


def test_get_json_schema():
    expected_schema = {"type": "string"}
    result = KernelJsonSchemaBuilder.get_json_schema(str)
    assert result == expected_schema

    expected_schema = {"type": "integer"}
    result = KernelJsonSchemaBuilder.get_json_schema(int)
    assert result == expected_schema
