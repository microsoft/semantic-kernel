# Copyright (c) Microsoft. All rights reserved.

from pydantic import Field

from semantic_kernel.sk_pydantic import SKBaseModel


class OpenAIToolOutput(SKBaseModel):
    """
    The OpenAIToolOutput class that is used to form responses back to the LLM
    when calling with tools. The original tool_call_id is required along with the
    output from the function call.
    """

    tool_call_id: str = Field(..., min_length=1, init_var=False)
    output: str = Field(..., min_length=1, init_var=False)
