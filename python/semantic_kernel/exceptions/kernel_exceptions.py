# Copyright (c) Microsoft. All rights reserved.


# Even though there is no strict separation between errors and exceptions in Python, it is a good practice to use:
# - Exceptions for exceptional conditions that a reasonable application may wish to catch.
# - Errors for exceptional conditions that are not reasonable to catch.
# for instance syntax errors in a template should be called ...Error,
# while rendering of the same template should raise an ...Exception.
# every error should derive from KernelException (including errors)
# all raised exceptions should use the raise ... from exc syntax to preserve the original traceback


class KernelException(Exception):
    """The base class for all Semantic Kernel exceptions."""

    pass


class KernelServiceNotFoundError(KernelException):
    """Raised when a service is not found in the kernel."""

    pass


class KernelPluginNotFoundError(KernelException):
    """Raised when a plugin is not found in the kernel."""

    pass


class KernelPluginInvalidConfigurationError(KernelException):
    """Raised when a plugin configuration is invalid."""

    pass


class KernelFunctionNotFoundError(KernelException):
    """Raised when a function is not found in the kernel."""

    pass


class KernelFunctionAlreadyExistsError(KernelException):
    """Raised when a function is already registered in the kernel."""

    pass


class KernelInvokeException(KernelException):
    """Raised when an error occurs while invoking a function in the kernel."""

    pass


class OperationCancelledException(KernelException):
    """Raised when an operation is cancelled."""

    pass


__all__ = [
    "KernelException",
    "KernelFunctionAlreadyExistsError",
    "KernelFunctionNotFoundError",
    "KernelInvokeException",
    "KernelPluginInvalidConfigurationError",
    "KernelPluginNotFoundError",
    "KernelServiceNotFoundError",
    "OperationCancelledException",
]
