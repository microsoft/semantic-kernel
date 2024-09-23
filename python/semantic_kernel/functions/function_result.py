# Copyright (c) Microsoft. All rights reserved.

import logging
<<<<<<< HEAD
from typing import Any
=======
from typing import Any, Mapping, Optional
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75

from pydantic import Field

from semantic_kernel.contents.kernel_content import KernelContent
<<<<<<< HEAD
from semantic_kernel.exceptions import FunctionResultError
=======
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.kernel_pydantic import KernelBaseModel

logger = logging.getLogger(__name__)


class FunctionResult(KernelBaseModel):
    """The result of a function.

<<<<<<< HEAD
    Args:
=======
    Arguments:
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
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
<<<<<<< HEAD
    metadata: dict[str, Any] = Field(default_factory=dict)
=======
    metadata: Mapping[str, Any] = Field(default_factory=dict)
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75

    def __str__(self) -> str:
        """Get the string representation of the result."""
        if self.value:
            try:
                if isinstance(self.value, list):
<<<<<<< HEAD
                    return (
                        str(self.value[0])
                        if isinstance(self.value[0], KernelContent)
                        else ",".join(map(str, self.value))
                    )
                if isinstance(self.value, dict):
                    # TODO (eavanvalkenburg): remove this once function result doesn't include input args
=======
                    return str(self.value[0])
                elif isinstance(self.value, dict):
                    # TODO: remove this once function result doesn't include input args
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
                    # This is so an integration test can pass.
                    return str(list(self.value.values())[-1])
                return str(self.value)
            except Exception as e:
<<<<<<< HEAD
                raise FunctionResultError(
                    f"Failed to convert value to string: {e}"
                ) from e
        else:
            return ""

    def get_inner_content(self, index: int = 0) -> Any | None:
        """Get the inner content of the function result.

        Args:
            index (int): The index of the inner content if the inner content is a list, default 0.
        """
        if isinstance(self.value, list) and isinstance(
            self.value[index], KernelContent
        ):
            return self.value[index].inner_content
=======
                logger.warning(f"Failed to convert value to string: {e}")
                raise e
        else:
            return ""

    def get_inner_content(self, index: int = 0) -> Optional[Any]:
        """Get the inner content of the function result.

        Arguments:
            index (int): The index of the inner content if the inner content is a list, default 0.
        """
        if isinstance(self.value, list):
            if isinstance(self.value[index], KernelContent):
                return self.value[index].inner_content
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
        if isinstance(self.value, KernelContent):
            return self.value.inner_content
        return None
