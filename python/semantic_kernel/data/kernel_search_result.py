# Copyright (c) Microsoft. All rights reserved.

from collections.abc import Mapping, Sequence
from typing import Any, Generic, TypeVar

from semantic_kernel.kernel_pydantic import KernelBaseModel

T = TypeVar("T")


class KernelSearchResult(KernelBaseModel, Generic[T]):
    """The result of a kernel search."""

    results: Sequence[T]
    total_count: int | None = None
    metadata: Mapping[str, Any] | None = None
