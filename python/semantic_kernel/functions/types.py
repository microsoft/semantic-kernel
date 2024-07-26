# Copyright (c) Microsoft. All rights reserved.

from collections.abc import Callable
from typing import Any, Union

from semantic_kernel.functions.kernel_function import KernelFunction

KERNEL_FUNCTION_TYPE = Union[KernelFunction, Callable[..., Any]]
