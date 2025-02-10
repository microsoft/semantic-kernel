# Copyright (c) Microsoft. All rights reserved.

from typing import Any

from pydantic import Field, model_validator

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.schema.kernel_json_schema_builder import KernelJsonSchemaBuilder
from semantic_kernel.utils.validation import FUNCTION_PARAM_NAME_REGEX


class KernelParameterMetadata(KernelBaseModel):
    """The kernel parameter metadata."""

    name: str | None = Field(..., pattern=FUNCTION_PARAM_NAME_REGEX)
    description: str | None = None
    default_value: Any | None = None
    type_: str | None = Field(default="str", alias="type")
    is_required: bool | None = False
    type_object: Any | None = None
    schema_data: dict[str, Any] | None = None
    include_in_function_choices: bool = True

    @model_validator(mode="before")
    @classmethod
    def form_schema(cls, data: Any) -> Any:
        """Create a schema for the parameter metadata."""
        if isinstance(data, dict) and data.get("schema_data") is None:
            type_object = data.get("type_object", None)
            type_ = data.get("type_", None)
            default_value = data.get("default_value", None)
            description = data.get("description", None)
            inferred_schema = cls.infer_schema(type_object, type_, default_value, description)
            data["schema_data"] = inferred_schema
        return data

    @classmethod
    def infer_schema(
        cls,
        type_object: type | None = None,
        parameter_type: str | None = None,
        default_value: Any | None = None,
        description: str | None = None,
        structured_output: bool = False,
    ) -> dict[str, Any] | None:
        """Infer the schema for the parameter metadata."""
        schema = None

        if type_object is not None:
            schema = KernelJsonSchemaBuilder.build(type_object, description, structured_output)
        elif parameter_type is not None:
            string_default = str(default_value) if default_value is not None else None
            if string_default and string_default.strip():
                needs_space = bool(description and description.strip())
                description = (
                    f"{description}{' ' if needs_space else ''}(default value: {string_default})"
                    if description
                    else f"(default value: {string_default})"
                )

            schema = KernelJsonSchemaBuilder.build_from_type_name(parameter_type, description)
        return schema
