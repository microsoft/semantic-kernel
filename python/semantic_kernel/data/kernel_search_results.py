# Copyright (c) Microsoft. All rights reserved.

from collections.abc import AsyncIterable, Mapping
from typing import Any, Generic, TypeVar

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.experimental_decorator import experimental_class

T = TypeVar("T")


@experimental_class
class KernelSearchResults(KernelBaseModel, Generic[T]):
    """The result of a kernel search."""

    results: AsyncIterable[T]
    total_count: int | None = None
    metadata: Mapping[str, Any] | None = None
