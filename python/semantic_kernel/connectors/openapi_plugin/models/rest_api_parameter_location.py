# Copyright (c) Microsoft. All rights reserved.

from enum import Enum

from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class RestApiParameterLocation(Enum):
    """The location of the REST API parameter."""

    PATH = "path"
    QUERY = "query"
    HEADER = "header"
    COOKIE = "cookie"
    BODY = "body"
