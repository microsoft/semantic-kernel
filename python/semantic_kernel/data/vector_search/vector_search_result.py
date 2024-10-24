# Copyright (c) Microsoft. All rights reserved.

from typing import Generic, TypeVar

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.experimental_decorator import experimental_class

TModel = TypeVar("TModel")


@experimental_class
class VectorSearchResult(KernelBaseModel, Generic[TModel]):
    """The result of a vector search."""

    record: TModel
    score: float | None = None
