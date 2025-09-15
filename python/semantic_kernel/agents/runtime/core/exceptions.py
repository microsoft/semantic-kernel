# Copyright (c) Microsoft. All rights reserved.

__all__ = ["CantHandleException", "MessageDroppedException", "NotAccessibleError", "UndeliverableException"]

from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class CantHandleException(Exception):
    """Raised when a handler can't handle the exception."""


@experimental
class UndeliverableException(Exception):
    """Raised when a message can't be delivered."""


@experimental
class MessageDroppedException(Exception):
    """Raised when a message is dropped."""


@experimental
class NotAccessibleError(Exception):
    """Tried to access a value that is not accessible. For example if it is remote cannot be accessed locally."""
