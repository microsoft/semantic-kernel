# Copyright (c) Microsoft. All rights reserved.


from semantic_kernel.exceptions.kernel_exceptions import KernelException


class ProcessException(KernelException):
    """Base class for all process exceptions."""

    pass


class ProcessInvalidConfigurationException(ProcessException):
    """An invalid configuration was provided for the process."""

    pass


class ProcessTargetFunctionNameMismatchException(ProcessException):
    """A message targeting a function has resulted in a different function becoming invocable."""

    pass


class ProcessFunctionNotFoundException(ProcessException):
    """A function was not found in the process."""

    pass


class ProcessEventUndefinedException(ProcessException):
    """An event was not defined in the process."""

    pass
