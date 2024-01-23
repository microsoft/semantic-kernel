# Copyright (c) Microsoft. All rights reserved.

from typing import Protocol, runtime_checkable

from semantic_kernel.orchestration.kernel_context import KernelContext


@runtime_checkable
class CodeRenderer(Protocol):
    """
    Protocol for dynamic code blocks that need async IO to be rendered.
    """

    async def render_code_async(self, context: KernelContext) -> str:
        """
        Render the block using the given context.

        :param context: kernel execution context
        :return: Rendered content
        """
        ...
