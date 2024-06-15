# Copyright (c) Microsoft. All rights reserved.

from enum import Enum

from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class RestApiOperationParameterLocation(Enum):
    """The location of the REST API operation parameter."""

    PATH = "path"
    QUERY = "query"
    HEADER = "header"
    COOKIE = "cookie"
    BODY = "body"
