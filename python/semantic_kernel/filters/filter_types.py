# Copyright (c) Microsoft. All rights reserved.

from enum import Enum

from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class FilterTypes(str, Enum):
    """Enum for the filter types."""

    FUNCTION_INVOCATION = "function_invocation"
    PROMPT_RENDERING = "prompt_rendering"
    AUTO_FUNCTION_INVOCATION = "auto_function_invocation"
