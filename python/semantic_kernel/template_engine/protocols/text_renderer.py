# Copyright (c) Microsoft. All rights reserved.

from abc import abstractmethod
from typing import TYPE_CHECKING, Optional, Protocol, runtime_checkable

if TYPE_CHECKING:
    from semantic_kernel import Kernel
    from semantic_kernel.functions.kernel_arguments import KernelArguments


@runtime_checkable
class TextRenderer(Protocol):
    """Protocol for static (text) blocks that don't need async rendering."""

    @abstractmethod
    def render(self, kernel: "Kernel", arguments: Optional["KernelArguments"] = None) -> str:
        """Render the block using only the given variables.

        :param variables: Optional variables used to render the block
        :return: Rendered content
        """
