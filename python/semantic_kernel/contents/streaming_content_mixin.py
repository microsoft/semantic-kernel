# Copyright (c) Microsoft. All rights reserved.
import sys
from abc import ABC, abstractmethod

from semantic_kernel.contents.finish_reason import FinishReason

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

from typing import Any, Optional

from semantic_kernel.kernel_pydantic import KernelBaseModel


class StreamingContentMixin(KernelBaseModel, ABC):
    """Mixin class for all streaming kernel contents."""

    choice_index: int
    finish_reason: Optional[FinishReason] = None

    @abstractmethod
    def __bytes__(self) -> bytes:
        pass

    @abstractmethod
    def __add__(self, other: Any) -> Self:
        pass
