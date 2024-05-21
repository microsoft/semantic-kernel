# Copyright (c) Microsoft. All rights reserved.

from typing import Any, get_type_hints

from semantic_kernel.kernel_pydantic import KernelBaseModel

TYPE_MAPPING = {
    int: "integer",
    str: "string",
    bool: "boolean",
    float: "number",
    list: "array",
    dict: "object",
    "int": "integer",
    "str": "string",
    "bool": "boolean",
    "float": "number",
    "list": "array",
    "dict": "object",
    "object": "object",
}


class KernelJsonSchemaBuilder:

    @classmethod
    def build(cls, parameter_type: type | str, description: str | None = None) -> dict[str, Any]:
        """Builds JSON schema for a given parameter type."""
        print(f"Building schema for type: {parameter_type}")

        if isinstance(parameter_type, str):
            return cls.build_from_type_name(parameter_type, description)
        if issubclass(parameter_type, KernelBaseModel):
            return cls.build_model_schema(parameter_type, description)
        if hasattr(parameter_type, "__annotations__"):
            return cls.build_model_schema(parameter_type, description)
        else:
            schema = cls.get_json_schema(parameter_type)
            if description:
                schema["description"] = description
            return schema

    @classmethod
    def build_model_schema(cls, model: type, description: str | None = None) -> dict[str, Any]:
        """Builds JSON schema for a given model."""
        properties = {}
        for field_name, field_type in get_type_hints(model).items():
            field_description = None
            if hasattr(model, "__fields__") and field_name in model.__fields__:
                field_info = model.__fields__[field_name]
                field_description = field_info.description
            properties[field_name] = cls.build(field_type, field_description)

        schema = {"type": "object", "properties": properties}

        if description:
            schema["description"] = description

        print(f"Generated schema for model {model}: {schema}")
        return schema

    @classmethod
    def build_from_type_name(cls, parameter_type: str, description: str | None = None) -> dict[str, Any]:
        """Builds JSON schema for a given parameter type name."""
        type_name = TYPE_MAPPING.get(parameter_type, "object")
        schema = {"type": type_name}
        if description:
            schema["description"] = description

        print(f"Generated schema from type name {parameter_type}: {schema}")
        return schema

    @classmethod
    def get_json_schema(cls, parameter_type: type) -> dict[str, Any]:
        """Gets JSON schema for a given parameter type."""
        type_name = TYPE_MAPPING.get(parameter_type, "object")
        schema = {"type": type_name}
        print(f"Generated JSON schema for type {parameter_type}: {schema}")
        return schema
