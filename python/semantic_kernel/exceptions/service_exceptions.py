# Copyright (c) Microsoft. All rights reserved.


from semantic_kernel.exceptions.kernel_exceptions import KernelException


class ServiceException(KernelException):
    """Base class for all service exceptions."""

    pass


class ServiceInitializationError(ServiceException):
    """An error occurred while initializing the service."""

    pass


class ServiceResponseException(ServiceException):
    """Base class for all service response exceptions."""

    pass


class ServiceInvalidAuthError(ServiceException):
    """An error occurred while authenticating the service."""

    pass


class ServiceInvalidTypeError(ServiceResponseException):
    """An error occurred while validating the type of the service request."""

    pass


class ServiceInvalidRequestError(ServiceResponseException):
    """An error occurred while validating the request to the service."""

    pass


class ServiceInvalidResponseError(ServiceResponseException):
    """An error occurred while validating the response from the service."""

    pass


class ServiceInvalidExecutionSettingsError(ServiceResponseException):
    """An error occurred while validating the execution settings of the service."""

    pass


class ServiceContentFilterException(ServiceResponseException):
    """An error was raised by the content filter of the service."""

    pass


class ServiceResourceNotFoundError(ServiceException):
    """The request service could not be found."""

    pass


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
