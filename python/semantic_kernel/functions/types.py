# Copyright (c) Microsoft. All rights reserved.

from typing import Any, Callable, Union

from semantic_kernel.functions.kernel_function import KernelFunction

KERNEL_FUNCTION_TYPE = Union[KernelFunction, Callable[..., Any]]
