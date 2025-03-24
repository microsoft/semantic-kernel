# Copyright (c) Microsoft. All rights reserved.
from semantic_kernel.kernel_pydantic import KernelBaseModel


class MCPToolParameters(KernelBaseModel):
    """Semantic Kernel Class for MCP Tool Parameters."""

    name: str
    type: str
    required: bool = False
    default_value: str | int | float = None
    items: dict | None = None
