# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class TextSearchResult(KernelBaseModel):
    """The result of a text search."""

    name: str | None = None
    value: str | None = None
    link: str | None = None
