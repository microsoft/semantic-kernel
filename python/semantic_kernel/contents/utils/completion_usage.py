# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.kernel_pydantic import KernelBaseModel


class KernelCompletionUsage(KernelBaseModel):
    """A usage example for the completion agent."""

    completion_tokens: int
    prompt_tokens: int
    total_tokens: int
