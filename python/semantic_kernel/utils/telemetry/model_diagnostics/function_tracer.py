# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING, Any

from opentelemetry import trace

from semantic_kernel.utils.telemetry.model_diagnostics.gen_ai_attributes import (
    OPERATION,
    TOOL_CALL_ID,
    TOOL_DESCRIPTION,
    TOOL_NAME,
)

if TYPE_CHECKING:
    from semantic_kernel.functions.kernel_function import KernelFunction


# The operation name is defined by OTeL GenAI semantic conventions:
# https://opentelemetry.io/docs/specs/semconv/gen-ai/gen-ai-spans/#execute-tool-span
OPERATION_NAME = "execute_tool"


def start_as_current_span(
    tracer: trace.Tracer,
    function: "KernelFunction",
    metadata: dict[str, Any] | None = None,
):
    """Starts a span for the given function using the provided tracer.

    Args:
        tracer (trace.Tracer): The OpenTelemetry tracer to use.
        function (KernelFunction): The function for which to start the span.
        metadata (dict[str, Any] | None): Optional metadata to include in the span attributes.

    Returns:
        trace.Span: The started span as a context manager.
    """
    attributes = {
        OPERATION: OPERATION_NAME,
        TOOL_NAME: function.fully_qualified_name,
    }

    tool_call_id = metadata.get("id", None) if metadata else None
    if tool_call_id:
        attributes[TOOL_CALL_ID] = tool_call_id
    if function.description:
        attributes[TOOL_DESCRIPTION] = function.description

    return tracer.start_as_current_span(f"{OPERATION_NAME} {function.fully_qualified_name}", attributes=attributes)
