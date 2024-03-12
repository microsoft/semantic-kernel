"""
Exceptions that are specific to the cloudsearch2 module.
"""
from boto.exception import BotoServerError


class InvalidTypeException(BotoServerError):
    """
    Raised when an invalid record type is passed to CloudSearch.
    """
    pass


class LimitExceededException(BotoServerError):
    """
    Raised when a limit has been exceeded.
    """
    pass


class InternalException(BotoServerError):
    """
    A generic server-side error.
    """
    pass


class DisabledOperationException(BotoServerError):
    """
    Raised when an operation has been disabled.
    """
    pass


class ResourceNotFoundException(BotoServerError):
    """
    Raised when a requested resource does not exist.
    """
    pass


class BaseException(BotoServerError):
    """
    A generic server-side error.
    """
    pass
