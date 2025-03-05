# Copyright (c) Microsoft. All rights reserved.

from typing import Any

from pydantic import Field

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class LocalMessage(KernelBaseModel):
    """A message that is local to a namespace."""

    source_id: str = Field(...)
    destination_id: str = Field(...)
    function_name: str = Field(...)
    values: dict[str, Any | None] = Field(...)
    target_event_id: str | None = Field(None)
    target_event_data: Any | None = Field(None)
