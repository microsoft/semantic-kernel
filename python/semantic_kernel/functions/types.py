# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

from collections.abc import Callable
from typing import Any

from semantic_kernel.functions.kernel_function import KernelFunction

KERNEL_FUNCTION_TYPE = KernelFunction | Callable[..., Any]
