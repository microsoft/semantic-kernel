# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.connectors.ai.anthropic.services.utils import kernel_function_metadata_to_function_call_format
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata


def test_function_call_format_skips_params_excluded_from_function_choices() -> None:
    metadata = KernelFunctionMetadata(
        name="lookup",
        description="Look up a user",
        is_prompt=False,
        parameters=[
            KernelParameterMetadata(
                name="query", description="What to look up", schema_data={"type": "string"}, is_required=True
            ),
            KernelParameterMetadata(
                name="token",
                description="Internal",
                schema_data={"type": "string"},
                is_required=True,
                include_in_function_choices=False,
            ),
        ],
    )

    result = kernel_function_metadata_to_function_call_format(metadata)

    assert list(result["input_schema"]["properties"]) == ["query"]
    assert result["input_schema"]["required"] == ["query"]
