# Copyright (c) Microsoft. All rights reserved.

from typing import Any

from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata


def kernel_function_metadata_to_function_call_format(
    metadata: KernelFunctionMetadata,
) -> dict[str, Any]:
    """Convert the kernel function metadata to function calling format."""
    return {
        "type": "function",
        "function": {
            "name": metadata.fully_qualified_name,
            "description": metadata.description or "",
            "parameters": {
                "type": "object",
                "properties": {param.name: param.schema_data for param in metadata.parameters if param.is_required},
                "required": [p.name for p in metadata.parameters if p.is_required],
            },
        },
    }
