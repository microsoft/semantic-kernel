# Copyright (c) Microsoft. All rights reserved.

import types
from enum import Enum
from typing import Any, Union, get_args, get_origin, get_type_hints

from semantic_kernel.const import PARSED_ANNOTATION_UNION_DELIMITER
from semantic_kernel.exceptions.function_exceptions import (
    FunctionInvalidParameterConfiguration,
)
from semantic_kernel.kernel_pydantic import KernelBaseModel

TYPE_MAPPING = {
    int: "integer",
    str: "string",
    bool: "boolean",
    float: "number",
    list: "array",
    dict: "object",
    set: "array",
    tuple: "array",
    "int": "integer",
    "str": "string",
    "bool": "boolean",
    "float": "number",
    "list": "array",
    "dict": "object",
    "set": "array",
    "tuple": "array",
    "object": "object",
    "array": "array",
}


class KernelJsonSchemaBuilder:
    """Kernel JSON schema builder."""

    @classmethod
    def build(
        cls, parameter_type: type | str, description: str | None = None
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
        cls, parameter_type: type | str | Any, description: str | None = None, structured_output: bool = False
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        cls, parameter_type: type | str | Any, description: str | None = None, structured_output: bool = False
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
        cls, parameter_type: type | str | Any, description: str | None = None, structured_output: bool = False
>>>>>>> main
>>>>>>> Stashed changes
    ) -> dict[str, Any]:
        """Builds the JSON schema for a given parameter type and description.

        Args:
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            parameter_type (type | str): The parameter type.
            description (str, optional): The description of the parameter. Defaults to None.
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
            parameter_type (type | str): The parameter type.
            description (str, optional): The description of the parameter. Defaults to None.
=======
            parameter_type: The parameter type.
            description: The description of the parameter. Defaults to None.
            structured_output: Whether the outputs are structured. Defaults to False.
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
            parameter_type: The parameter type.
            description: The description of the parameter. Defaults to None.
            structured_output: Whether the outputs are structured. Defaults to False.
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes

        Returns:
            dict[str, Any]: The JSON schema for the parameter type.
        """
        if isinstance(parameter_type, str):
            return cls.build_from_type_name(parameter_type, description)
        if isinstance(parameter_type, KernelBaseModel):
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
            return cls.build_model_schema(parameter_type, description)
        if isinstance(parameter_type, type) and issubclass(parameter_type, Enum):
            return cls.build_enum_schema(parameter_type, description)
        if hasattr(parameter_type, "__annotations__"):
            return cls.build_model_schema(parameter_type, description)
        if hasattr(parameter_type, "__args__"):
            return cls.handle_complex_type(parameter_type, description)
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
            return cls.build_model_schema(parameter_type, description, structured_output)
        if isinstance(parameter_type, type) and issubclass(parameter_type, Enum):
            return cls.build_enum_schema(parameter_type, description)
        if hasattr(parameter_type, "__annotations__"):
            return cls.build_model_schema(parameter_type, description, structured_output)
        if hasattr(parameter_type, "__args__"):
            return cls.handle_complex_type(parameter_type, description, structured_output)
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
        schema = cls.get_json_schema(parameter_type)
        if description:
            schema["description"] = description
        return schema

    @classmethod
    def build_model_schema(
        cls, model: type, description: str | None = None
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
        cls, model: type | KernelBaseModel, description: str | None = None, structured_output: bool = False
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        cls, model: type | KernelBaseModel, description: str | None = None, structured_output: bool = False
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
        cls, model: type | KernelBaseModel, description: str | None = None, structured_output: bool = False
>>>>>>> main
>>>>>>> Stashed changes
    ) -> dict[str, Any]:
        """Builds the JSON schema for a given model and description.

        Args:
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            model (type): The model type.
            description (str, optional): The description of the model. Defaults to None.
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
            model (type): The model type.
            description (str, optional): The description of the model. Defaults to None.
=======
            model: The model type.
            description: The description of the model. Defaults to None.
            structured_output: Whether the outputs are structured. Defaults to False.
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
            model: The model type.
            description: The description of the model. Defaults to None.
            structured_output: Whether the outputs are structured. Defaults to False.
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes

        Returns:
            dict[str, Any]: The JSON schema for the model.
        """
        # TODO (moonbox3): add support for handling forward references, which is not currently tested
        # https://github.com/microsoft/semantic-kernel/issues/6464
        properties = {}
        required = []
        hints = get_type_hints(model, globals(), locals())

        for field_name, field_type in hints.items():
            field_description = None
            if hasattr(model, "model_fields") and field_name in model.model_fields:
                field_info = model.model_fields[field_name]
                if isinstance(field_info.metadata, dict):
                    field_description = field_info.metadata.get("description")
                elif isinstance(field_info.metadata, list) and field_info.metadata:
                    field_description = field_info.metadata[0]
                elif hasattr(field_info, "description"):
                    field_description = field_info.description
            if not cls._is_optional(field_type):
                required.append(field_name)
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            properties[field_name] = cls.build(field_type, field_description)
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
            properties[field_name] = cls.build(field_type, field_description)
=======
            properties[field_name] = cls.build(field_type, field_description, structured_output)
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
            properties[field_name] = cls.build(field_type, field_description, structured_output)
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes

        schema = {"type": "object", "properties": properties}
        if required:
            schema["required"] = required
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
        if structured_output:
            schema["additionalProperties"] = False  # type: ignore
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        if structured_output:
            schema["additionalProperties"] = False  # type: ignore
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
        if description:
            schema["description"] = description

        return schema

    @classmethod
    def _is_optional(cls, field_type: Any) -> bool:
        return get_origin(field_type) in {types.UnionType, Union} and type(
            None
        ) in get_args(field_type)

    @classmethod
    def build_from_type_name(
        cls, parameter_type: str, description: str | None = None
    ) -> dict[str, Any]:
        """Builds the JSON schema for a given parameter type name and description.

        Args:
            parameter_type (str): The parameter type name.
            description (str, optional): The description of the parameter. Defaults to None.

        Returns:
            dict[str, Any]: The JSON schema for the parameter type.
        """
        schema: dict[str, Any] = {}
        if PARSED_ANNOTATION_UNION_DELIMITER in parameter_type:
            # this means it is a Union or | so need to build with "anyOf"
            types = parameter_type.split(PARSED_ANNOTATION_UNION_DELIMITER)
            schemas = [cls.build_from_type_name(t.strip(), description) for t in types]
            schema["anyOf"] = schemas
        else:
            type_name = TYPE_MAPPING.get(parameter_type, "object")
            schema["type"] = type_name
            if description:
                schema["description"] = description
        return schema

    @classmethod
    def get_json_schema(cls, parameter_type: type) -> dict[str, Any]:
        """Gets JSON schema for a given parameter type.

        Args:
            parameter_type (type): The parameter type.

        Returns:
            dict[str, Any]: The JSON schema for the parameter type.
        """
        type_name = TYPE_MAPPING.get(parameter_type, "object")
        return {"type": type_name}

    @classmethod
    def handle_complex_type(
        cls, parameter_type: type, description: str | None = None
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
        cls, parameter_type: type, description: str | None = None, structured_output: bool = False
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        cls, parameter_type: type, description: str | None = None, structured_output: bool = False
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
        cls, parameter_type: type, description: str | None = None, structured_output: bool = False
>>>>>>> main
>>>>>>> Stashed changes
    ) -> dict[str, Any]:
        """Handles building the JSON schema for complex types.

        Args:
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            parameter_type (type): The parameter type.
            description (str, optional): The description of the parameter. Defaults to None.
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
            parameter_type (type): The parameter type.
            description (str, optional): The description of the parameter. Defaults to None.
=======
            parameter_type: The parameter type.
            description: The description of the parameter. Defaults to None.
            structured_output: Whether the outputs are structured. Defaults to False.
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
            parameter_type: The parameter type.
            description: The description of the parameter. Defaults to None.
            structured_output: Whether the outputs are structured. Defaults to False.
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes

        Returns:
            dict[str, Any]: The JSON schema for the parameter type.
        """
        origin = get_origin(parameter_type)
        args = get_args(parameter_type)

        schema: dict[str, Any] = {}
        if origin is list or origin is set:
            item_type = args[0]
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            schema = {"type": "array", "items": cls.build(item_type)}
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
            schema = {"type": "array", "items": cls.build(item_type)}
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
            schema = {"type": "array", "items": cls.build(item_type)}
=======
>>>>>>> Stashed changes
            schema = {
                "type": "array",
                "items": cls.build(item_type, structured_output=structured_output),
            }
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
            if description:
                schema["description"] = description
            return schema
        if origin is dict:
            _, value_type = args
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
            additional_properties = cls.build(value_type)
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
            additional_properties = cls.build(value_type)
=======
            additional_properties = cls.build(value_type, structured_output=structured_output)
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
            additional_properties = cls.build(value_type, structured_output=structured_output)
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
            if additional_properties == {"type": "object"}:
                additional_properties["properties"] = (
                    {}
                )  # Account for differences in Python 3.10 dict
            schema = {"type": "object", "additionalProperties": additional_properties}
            if description:
                schema["description"] = description
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
            return schema
        if origin is tuple:
            items = [cls.build(arg) for arg in args]
            schema = {"type": "array", "items": items}
            if description:
                schema["description"] = description
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
            if structured_output:
                schema["additionalProperties"] = False
            return schema
        if origin is tuple:
            items = [cls.build(arg, structured_output=structured_output) for arg in args]
            schema = {"type": "array", "items": items}
            if description:
                schema["description"] = description
            if structured_output:
                schema["additionalProperties"] = False
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
            return schema
        if origin in {Union, types.UnionType}:
            # Handle Optional[T] (Union[T, None]) by making schema nullable
            if len(args) == 2 and type(None) in args:
                non_none_type = args[0] if args[1] is type(None) else args[1]
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
                schema = cls.build(non_none_type)
                schema["type"] = [schema["type"], "null"]
                if description:
                    schema["description"] = description
                return schema
            schemas = [cls.build(arg, description) for arg in args]
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
                schema = cls.build(non_none_type, structured_output=structured_output)
                schema["type"] = [schema["type"], "null"]
                if description:
                    schema["description"] = description
                if structured_output:
                    schema["additionalProperties"] = False
                return schema
            schemas = [cls.build(arg, description, structured_output=structured_output) for arg in args]
<<<<<<< Updated upstream
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> main
>>>>>>> Stashed changes
            return {"anyOf": schemas}
        schema = cls.get_json_schema(parameter_type)
        if description:
            schema["description"] = description
<<<<<<< HEAD
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
=======
        if structured_output:
            schema["additionalProperties"] = False
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
        if structured_output:
            schema["additionalProperties"] = False
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
        return schema

    @classmethod
    def build_enum_schema(
        cls, enum_type: type, description: str | None = None
    ) -> dict[str, Any]:
        """Builds the JSON schema for an enum type.

        Args:
            enum_type (type): The enum type.
            description (str, optional): The description of the enum. Defaults to None.

        Returns:
            dict[str, Any]: The JSON schema for the enum type.
        """
        if not issubclass(enum_type, Enum):
            raise FunctionInvalidParameterConfiguration(
                f"{enum_type} is not a valid Enum type"
            )

        try:
            enum_values = [item.value for item in enum_type]
        except TypeError as ex:
            raise FunctionInvalidParameterConfiguration(
                f"Failed to get enum values for {enum_type}"
            ) from ex
        schema = {
            "type": TYPE_MAPPING.get(type(enum_values[0]), "string"),
            "enum": enum_values,
        }
        if description:
            schema["description"] = description
        return schema
