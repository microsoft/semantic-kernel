import logging
from typing import TYPE_CHECKING, Any, Mapping, Optional

from pydantic import Field

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.models.contents.kernel_content import KernelContent

if TYPE_CHECKING:
    from semantic_kernel.orchestration.kernel_function import KernelFunction


logger = logging.getLogger(__name__)


class FunctionResult(KernelBaseModel):
    function: "KernelFunction"
    value: Any
    metadata: Mapping[str, Any] = Field(default_factory=dict)

    def __str__(self) -> Optional[str]:
        if self.value:
            try:
                return str(self.value)
            except Exception as e:
                logger.warning(f"Failed to convert value to string: {e}")
                raise e
        else:
            return None

    @property
    def inner_content(self) -> Optional[Any]:
        if isinstance(self.value, KernelContent):
            return self.value.inner_content
        return None
