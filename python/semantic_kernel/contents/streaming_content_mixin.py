# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

import sys
from abc import ABC, abstractmethod

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

from typing import Any

from semantic_kernel.kernel_pydantic import KernelBaseModel


class StreamingContentMixin(KernelBaseModel, ABC):
    """Mixin class for all streaming kernel contents."""

    choice_index: int

    @abstractmethod
    def __bytes__(self) -> bytes:
        pass

    @abstractmethod
    def __add__(self, other: Any) -> Self:
        pass
