# Copyright (c) Microsoft. All rights reserved.

from abc import abstractmethod
from typing import TYPE_CHECKING, Protocol, runtime_checkable

if TYPE_CHECKING:
    from semantic_kernel import Kernel
    from semantic_kernel.functions.kernel_arguments import KernelArguments


@runtime_checkable
class CodeRenderer(Protocol):
    """Protocol for dynamic code blocks that need async IO to be rendered."""

    @abstractmethod
    async def render_code(self, kernel: "Kernel", arguments: "KernelArguments") -> str:
        """Render the block using the given context.

        :param context: kernel execution context
        :return: Rendered content
        """
