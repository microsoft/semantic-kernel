# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import Any

from pydantic import Field

from semantic_kernel.contents.kernel_content import KernelContent
from semantic_kernel.exceptions import FunctionResultError
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.kernel_pydantic import KernelBaseModel

logger = logging.getLogger(__name__)


class FunctionResult(KernelBaseModel):
    """The result of a function.

    Args:
        function (KernelFunctionMetadata): The metadata of the function that was invoked.
        value (Any): The value of the result.
        metadata (Mapping[str, Any]): The metadata of the result.

    Methods:
        __str__: Get the string representation of the result, will call str() on the value,
            or if the value is a list, will call str() on the first element of the list.
        get_inner_content: Get the inner content of the function result
            when that is a KernelContent or subclass of the first item of the value if it is a list.

    """

    function: KernelFunctionMetadata
    value: Any
    metadata: dict[str, Any] = Field(default_factory=dict)

    def __str__(self) -> str:
        """Get the string representation of the result."""
        if self.value:
            try:
                if isinstance(self.value, list):
                    return (
                        str(self.value[0])
                        if isinstance(self.value[0], KernelContent)
                        else ",".join(map(str, self.value))
                    )
                if isinstance(self.value, dict):
                    # TODO (eavanvalkenburg): remove this once function result doesn't include input args
                    # This is so an integration test can pass.
                    return str(list(self.value.values())[-1])
                return str(self.value)
            except Exception as e:
                raise FunctionResultError(f"Failed to convert value to string: {e}") from e
        else:
            return ""

    def get_inner_content(self, index: int = 0) -> Any | None:
        """Get the inner content of the function result.

        Args:
            index (int): The index of the inner content if the inner content is a list, default 0.
        """
        if isinstance(self.value, list) and isinstance(self.value[index], KernelContent):
            return self.value[index].inner_content
        if isinstance(self.value, KernelContent):
            return self.value.inner_content
        return None
