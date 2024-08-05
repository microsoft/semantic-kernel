# Copyright (c) Microsoft. All rights reserved.

from enum import Enum

from semantic_kernel.utils.experimental_decorator import experimental_class


@experimental_class
class RestApiOperationParameterStyle(Enum):
    SIMPLE = "simple"
