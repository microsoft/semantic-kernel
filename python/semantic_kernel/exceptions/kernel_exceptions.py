# Copyright (c) Microsoft. All rights reserved.


# Even though there is no strict separation between errors and exceptions in Python, it is a good practice to use:
# - Exceptions for exceptional conditions that a reasonable application may wish to catch.
# - Errors for exceptional conditions that are not reasonable to catch.
# for instance syntax errors in a template should be called ...Error,
# while rendering of the same template should raise an ...Exception.
# every error should derive from KernelException (including errors)
# all raised exceptions should use the raise ... from exc syntax to preserve the original traceback


class KernelException(Exception):
    pass


class KernelServiceNotFoundError(KernelException):
    pass


class KernelPluginNotFoundError(KernelException):
    pass


class KernelFunctionNotFoundError(KernelException):
    pass


class KernelFunctionAlreadyExistsError(KernelException):
    pass


class KernelInvokeException(KernelException):
    pass


__all__ = [
    "KernelException",
    "KernelFunctionAlreadyExistsError",
    "KernelFunctionNotFoundError",
    "KernelInvokeException",
    "KernelPluginNotFoundError",
    "KernelServiceNotFoundError",
]
