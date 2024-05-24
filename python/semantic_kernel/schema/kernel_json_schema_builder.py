from typing import Any, Union, get_args, get_origin, get_type_hints

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

    @classmethod
    def build(cls, parameter_type: type | str, description: str | None = None) -> dict[str, Any]:
        """Builds JSON schema for a given parameter type."""

        if isinstance(parameter_type, str):
            return cls.build_from_type_name(parameter_type, description)
        if isinstance(parameter_type, KernelBaseModel):
            return cls.build_model_schema(parameter_type, description)
        if hasattr(parameter_type, "__annotations__"):
            return cls.build_model_schema(parameter_type, description)
        if hasattr(parameter_type, "__args__"):
            return cls.handle_complex_type(parameter_type, description)
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

        return schema

    @classmethod
    def build_from_type_name(cls, parameter_type: str, description: str | None = None) -> dict[str, Any]:
        """Builds JSON schema for a given parameter type name."""
        type_name = TYPE_MAPPING.get(parameter_type, "object")
        schema = {"type": type_name}
        if description:
            schema["description"] = description

        return schema

    @classmethod
    def get_json_schema(cls, parameter_type: type) -> dict[str, Any]:
        """Gets JSON schema for a given parameter type."""
        type_name = TYPE_MAPPING.get(parameter_type, "object")
        schema = {"type": type_name}
        return schema

    @classmethod
    def handle_complex_type(cls, parameter_type: type, description: str | None = None) -> dict[str, Any]:
        """Handles complex types like list[str], dict[str, int],
        set[int], tuple[int, str], Union[int, str], and Optional[int]."""
        origin = get_origin(parameter_type)
        args = get_args(parameter_type)

        if origin is list or origin is set:
            item_type = args[0]
            return {"type": "array", "items": cls.build(item_type), "description": description}
        elif origin is dict:
            _, value_type = args
            return {"type": "object", "additionalProperties": cls.build(value_type), "description": description}
        elif origin is tuple:
            items = [cls.build(arg) for arg in args]
            return {"type": "array", "items": items, "description": description}
        elif origin is Union:
            if len(args) == 2 and type(None) in args:
                non_none_type = args[0] if args[1] is type(None) else args[1]
                schema = cls.build(non_none_type)
                schema["nullable"] = True
                if description:
                    schema["description"] = description
                return schema
            else:
                schemas = [cls.build(arg) for arg in args]
                return {"anyOf": schemas, "description": description}
        else:
            return cls.get_json_schema(parameter_type)
