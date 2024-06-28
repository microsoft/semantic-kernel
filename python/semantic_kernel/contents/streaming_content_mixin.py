# Copyright (c) Microsoft. All rights reserved.

import sys
from abc import ABC, abstractmethod
from typing import Any

if sys.version_info >= (3, 11):
    from typing import Self  # pragma: no cover
else:
    from typing_extensions import Self  # pragma: no cover

from semantic_kernel.kernel_pydantic import KernelBaseModel


class StreamingContentMixin(KernelBaseModel, ABC):
    """Mixin class for all streaming kernel contents."""

    choice_index: int

    @abstractmethod
    def __bytes__(self) -> bytes:
        """Return the content of the response encoded in the encoding."""
        pass

    @abstractmethod
    def __add__(self, other: Any) -> Self:
        """Combine two streaming contents together."""
        pass
