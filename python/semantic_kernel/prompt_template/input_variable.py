# Copyright (c) Microsoft. All rights reserved.

from typing import Any

from semantic_kernel.kernel_pydantic import KernelBaseModel


class InputVariable(KernelBaseModel):
    """Input variable for a prompt template.

    Args:
        name: The name of the input variable.
        description: The description of the input variable.
        default: The default value of the input variable.
        is_required: Whether the input variable is required.
        json_schema: The JSON schema for the input variable.
        allow_dangerously_set_content: Allow content without encoding, this controls
            if this variable is encoded before use, default is False.
    """

    name: str
    description: str | None = ""
    default: Any | None = ""
    is_required: bool | None = True
    json_schema: str | None = ""
    allow_dangerously_set_content: bool = False
