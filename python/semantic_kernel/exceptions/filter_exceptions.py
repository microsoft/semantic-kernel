# Copyright (c) Microsoft. All rights reserved.
from semantic_kernel.exceptions.kernel_exceptions import KernelException


class FilterException(KernelException):
    """Base class for all filter exceptions."""

    pass


class FilterManagementException(FilterException):
    """An error occurred while adding or removing the filter to/from the kernel."""

    pass


__all__ = [
    "FilterException",
    "FilterManagementException",
]
