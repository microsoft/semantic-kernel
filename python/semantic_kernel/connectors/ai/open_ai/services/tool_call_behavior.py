# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.kernel_pydantic import KernelBaseModel


class ToolCallBehavior(KernelBaseModel):
    """
    This, at its start, is a very slim class. The reason that this class is necessary
    is because during auto invoking function calls for OpenAI streaming chat completions,
    we need a way to toggle a boolean to kick us out of the async generator/loop that is started
    related to the max auto invoke attempts. Booleans are immutable therefore if its state is
    changed inside a method, we're creating a new boolean, which is not what we want. By wrapping
    this flag inside of a class, when we do change its state, it is reflected outside of the method.
    """

    auto_invoke_kernel_functions: bool = False
    max_auto_invoke_attempts: int = 1
