# Copyright (c) Microsoft. All rights reserved.

from pydantic import Field

from semantic_kernel.kernel_pydantic import KernelBaseModel


class InputTokensDetails(KernelBaseModel):
    """Details about the Response input tokens."""

    cached_tokens: int = Field(..., description="The number of cached tokens.")


class OutputTokensDetails(KernelBaseModel):
    """Details about the Response output tokens."""

    reasoning_tokens: int = Field(..., description="The number of reasoning tokens.")


class ResponseUsage(KernelBaseModel):
    """Details about the Response usage."""

    input_tokens: int = Field(..., description="The number of input tokens.")
    input_tokens_details: InputTokensDetails = Field(..., description="Details about the input tokens.")
    output_tokens: int = Field(..., description="The number of output tokens.")
    output_tokens_details: OutputTokensDetails = Field(..., description="Details about the output tokens.")
    total_tokens: int = Field(..., description="The total number of tokens used.")
