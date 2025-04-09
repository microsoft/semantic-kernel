# Copyright (c) Microsoft. All rights reserved.

from typing import Any


def generate_structured_output_response_format_schema(name: str, schema: dict[str, Any]) -> dict[str, Any]:
    """Generate the structured output response format schema."""
    return {
        "type": "json_schema",
        "json_schema": {"name": name, "strict": True, "schema": schema},
    }
