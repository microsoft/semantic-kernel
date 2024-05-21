# Copyright (c) Microsoft. All rights reserved.

import json
from typing import Any

from pydantic import ConfigDict

from semantic_kernel.kernel_pydantic import KernelBaseModel


class KernelJsonSchema(KernelBaseModel):
    inferred: bool = False
    schema_data: dict[str, Any] | None = None

    model_config = ConfigDict(json_encoders={dict: lambda v: json.dumps(v, indent=2)})

    @classmethod
    def parse_or_null(cls, json_schema: str | None) -> "KernelJsonSchema" | None:
        """Parses a JSON schema or returns None if the input is null or empty."""
        if json_schema and json_schema.strip():
            try:
                parsed_schema = json.loads(json_schema)
                return KernelJsonSchema(inferred=False, schema_data=parsed_schema)
            except json.JSONDecodeError:
                return None
        return None

    @classmethod
    def parse(cls, json_schema: str) -> "KernelJsonSchema":
        """Parses a JSON schema."""
        if not json_schema:
            raise ValueError("json_schema cannot be null or empty")
        try:
            parsed_schema = json.loads(json_schema)
            return KernelJsonSchema(inferred=False, schema_data=parsed_schema)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON: {e}")

    def to_json(self) -> str:
        """Converts the JSON schema to a JSON string."""
        return json.dumps(self.schema_data, indent=2)

    def __str__(self) -> str:
        """Converts the JSON schema to a string."""
        return self.to_json()
