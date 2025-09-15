# Copyright (c) Microsoft. All rights reserved.

from enum import Enum

from semantic_kernel.utils.feature_stage_decorator import experimental


@experimental
class RestApiParameterStyle(Enum):
    """RestApiParameterStyle."""

    SIMPLE = "simple"
