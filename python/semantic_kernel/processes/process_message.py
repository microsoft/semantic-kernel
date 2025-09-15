# Copyright (c) Microsoft. All rights reserved.

from typing import Any

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class ProcessMessage(KernelBaseModel):
    """Represents a message used in a process runtime."""

    source_id: str
    destination_id: str
    function_name: str
    values: dict[str, Any]

    target_event_id: str | None = None
    target_event_data: Any | None = None
