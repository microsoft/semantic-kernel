# Copyright (c) Microsoft. All rights reserved.

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List

from semantic_kernel.kernel_pydantic import KernelBaseModel

if TYPE_CHECKING:
    from semantic_kernel.orchestration.kernel_context import KernelContext
    from semantic_kernel.plugin_definition.parameter_view import ParameterView


class PromptTemplateBase(KernelBaseModel, ABC):
    @abstractmethod
    def get_parameters(self) -> List["ParameterView"]:
        pass

    @abstractmethod
    async def render(self, context: "KernelContext") -> str:
        pass
