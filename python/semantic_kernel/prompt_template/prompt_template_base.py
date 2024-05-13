# Copyright (c) Microsoft. All rights reserved.

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig

if TYPE_CHECKING:
    from semantic_kernel.functions.kernel_arguments import KernelArguments
    from semantic_kernel.kernel import Kernel


class PromptTemplateBase(KernelBaseModel, ABC):
    prompt_template_config: PromptTemplateConfig

    @abstractmethod
    async def render(self, kernel: "Kernel", arguments: "KernelArguments") -> str:
        pass
