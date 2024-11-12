# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class TextSearchResult(KernelBaseModel):
    """The result of a text search."""

    name: str | None = None
    value: str | None = None
    link: str | None = None
