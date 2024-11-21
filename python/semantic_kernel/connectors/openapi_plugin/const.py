# Copyright (c) Microsoft. All rights reserved.


from enum import Enum

from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class OperationExtensions(Enum):
    """The operation extensions."""

    METHOD_KEY = "method"
    OPERATION_KEY = "operation"
    INFO_KEY = "info"
    SECURITY_KEY = "security"
    SERVER_URLS_KEY = "server-urls"
    METADATA_KEY = "operation-extensions"
