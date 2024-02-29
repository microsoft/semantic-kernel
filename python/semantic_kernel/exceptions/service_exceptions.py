# Copyright (c) Microsoft. All rights reserved.


from semantic_kernel.exceptions.kernel_exceptions import KernelException


class ServiceException(KernelException):
    pass


class ServiceInitializationError(ServiceException):
    pass


class ServiceResponseException(ServiceException):
    pass


class ServiceInvalidAuthError(ServiceException):
    pass


class ServiceInvalidTypeError(ServiceResponseException):
    pass


class ServiceInvalidRequestError(ServiceResponseException):
    pass


class ServiceInvalidResponseError(ServiceResponseException):
    pass


class ServiceInvalidExecutionSettingsError(ServiceResponseException):
    pass


class ServiceContentFilterException(ServiceResponseException):
    pass


class ServiceResourceNotFoundError(ServiceException):
    pass


__all__ = [
    "ServiceException",
    "ServiceInvalidAuthError",
    "ServiceInitializationError",
    "ServiceResponseException",
    "ServiceInvalidTypeError",
    "ServiceInvalidRequestError",
    "ServiceInvalidResponseError",
    "ServiceInvalidExecutionSettingsError",
    "ServiceContentFilterException",
    "ServiceResourceNotFoundError",
]
