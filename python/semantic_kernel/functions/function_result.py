import logging
from typing import Any, Mapping, Optional

from pydantic import Field

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.contents.kernel_content import KernelContent

logger = logging.getLogger(__name__)


class FunctionResult(KernelBaseModel):
    function: Any
    value: Any
    metadata: Mapping[str, Any] = Field(default_factory=dict)

    def __str__(self) -> Optional[str]:
        if self.value:
            try:
                if isinstance(self.value, list):
                    return str(self.value[0])
                return str(self.value)
            except Exception as e:
                logger.warning(f"Failed to convert value to string: {e}")
                raise e
        else:
            return None

    def get_inner_content(self, index: int = 0) -> Optional[Any]:
        """Get the inner content of the function result.

        Arguments:
            index (int): The index of the inner content if the inner content is a list, default 0.
        """
        if isinstance(self.value, list):
            if isinstance(self.value[index], KernelContent):
                return self.value[index].inner_content
        if isinstance(self.value, KernelContent):
            return self.value.inner_content
        return None
