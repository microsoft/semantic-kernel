"""
Exceptions that are specific to the swf module.

This module subclasses the base SWF response exception, 
boto.exceptions.SWFResponseError, for some of the SWF specific faults.
"""
from boto.exception import SWFResponseError


class SWFDomainAlreadyExistsError(SWFResponseError):
    """
    Raised when when the domain already exists.
    """
    pass


class SWFLimitExceededError(SWFResponseError):
    """
    Raised when when a system imposed limitation has been reached.
    """
    pass


class SWFOperationNotPermittedError(SWFResponseError):
    """
    Raised when (reserved for future use).
    """


class SWFTypeAlreadyExistsError(SWFResponseError):
    """
    Raised when when the workflow type or activity type already exists.
    """
    pass


class SWFWorkflowExecutionAlreadyStartedError(SWFResponseError):
    """
    Raised when an open execution with the same workflow_id is already running
    in the specified domain.
    """



