# Copyright (c) Microsoft. All rights reserved.

TYPE_MAPPER = {
    "str": "string",
    "int": "number",
    "float": "number",
    "bool": "boolean",
    "list": "array",
    "dict": "object",
}


def parse_parameter_type(param_type: str | None) -> str:
    """Parse the parameter type."""
    if not param_type:
        return "string"
    if "," in param_type:
        param_type = param_type.split(",", maxsplit=1)[0]
    return TYPE_MAPPER.get(param_type, "string")
