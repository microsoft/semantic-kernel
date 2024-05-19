# Copyright (c) Microsoft. All rights reserved.

from typing import Any, Type, get_type_hints

from semantic_kernel.kernel_pydantic import KernelBaseModel


class KernelJsonSchemaBuilder:
    @staticmethod
    def build(parameter_type: Type, description: str | None = None) -> dict[str, Any]:
        """Builds JSON schema for a given parameter type."""
        if issubclass(parameter_type, KernelBaseModel):
            return KernelJsonSchemaBuilder.build_model_schema(parameter_type, description)
        elif hasattr(parameter_type, "__annotations__"):
            return KernelJsonSchemaBuilder.build_model_schema(parameter_type, description)
        else:
            schema = KernelJsonSchemaBuilder.get_json_schema(parameter_type)
            if description:
                schema["description"] = description
            return schema

    @staticmethod
    def build_model_schema(model: Type, description: str | None = None) -> dict[str, Any]:
        """Builds JSON schema for a given model."""
        properties = {}
        for field_name, field_type in get_type_hints(model).items():
            field_description = None
            if hasattr(model, "__fields__") and field_name in model.__fields__:
                field_info = model.__fields__[field_name]
                field_description = field_info.description
            properties[field_name] = KernelJsonSchemaBuilder.build(field_type, field_description)

        schema = {"type": "object", "properties": properties}

        if description:
            schema["description"] = description

        return schema

    @staticmethod
    def build_from_type_name(parameter_type: str, description: str | None = None) -> dict[str, Any]:
        """Builds JSON schema for a given parameter type name."""
        type_mapping = {
            "int": "integer",
            "str": "string",
            "bool": "boolean",
            "float": "number",
            "list": "array",
            "dict": "object",
            "object": "object",
        }
        type_name = type_mapping.get(parameter_type, "object")
        schema = {"type": type_name}
        if description:
            schema["description"] = description
        return schema

    @staticmethod
    def get_json_schema(parameter_type: Type) -> dict[str, Any]:
        """Gets JSON schema for a given parameter type."""
        type_mapping = {
            int: "integer",
            str: "string",
            bool: "boolean",
            float: "number",
            list: "array",
            dict: "object",
        }
        type_name = type_mapping.get(parameter_type, "object")
        schema = {"type": type_name}
        return schema
