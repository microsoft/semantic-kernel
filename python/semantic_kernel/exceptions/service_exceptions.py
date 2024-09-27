# Copyright (c) Microsoft. All rights reserved.


from semantic_kernel.exceptions.kernel_exceptions import KernelException


class ServiceException(KernelException):
    """Base class for all service exceptions."""


class ServiceInitializationError(ServiceException):
    """An error occurred while initializing the service."""


class ServiceResponseException(ServiceException):
    """Base class for all service response exceptions."""


class ServiceInvalidAuthError(ServiceException):
    """An error occurred while authenticating the service."""


class ServiceInvalidTypeError(ServiceResponseException):
    """An error occurred while validating the type of the service request."""


class ServiceInvalidRequestError(ServiceResponseException):
    """An error occurred while validating the request to the service."""


class ServiceInvalidResponseError(ServiceResponseException):
    """An error occurred while validating the response from the service."""


class ServiceInvalidExecutionSettingsError(ServiceResponseException):
    """An error occurred while validating the execution settings of the service."""


class ServiceContentFilterException(ServiceResponseException):
    """An error was raised by the content filter of the service."""


class ServiceResourceNotFoundError(ServiceException):
    """The request service could not be found."""


__all__ = [
    "ServiceContentFilterException",
    "ServiceException",
    "ServiceInitializationError",
    "ServiceInvalidAuthError",
    "ServiceInvalidExecutionSettingsError",
    "ServiceInvalidRequestError",
    "ServiceInvalidResponseError",
    "ServiceInvalidTypeError",
    "ServiceResourceNotFoundError",
    "ServiceResponseException",
]
