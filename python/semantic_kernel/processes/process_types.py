# Copyright (c) Microsoft. All rights reserved.

from typing import TypeVar

from semantic_kernel.processes.kernel_process.kernel_process_step import KernelProcessStep

TStep = TypeVar("TStep", bound=KernelProcessStep)
TState = TypeVar("TState")
