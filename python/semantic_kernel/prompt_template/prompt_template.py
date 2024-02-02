# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import TYPE_CHECKING, List

from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata
from semantic_kernel.prompt_template.prompt_template_base import PromptTemplateBase
from semantic_kernel.prompt_template.prompt_template_config import (
    PromptTemplateConfig,
)
from semantic_kernel.template_engine.blocks.block_types import BlockTypes
from semantic_kernel.template_engine.blocks.var_block import VarBlock
from semantic_kernel.template_engine.protocols.prompt_templating_engine import (
    PromptTemplatingEngine,
)

if TYPE_CHECKING:
    from semantic_kernel.functions.kernel_arguments import KernelArguments
    from semantic_kernel.kernel import Kernel

logger: logging.Logger = logging.getLogger(__name__)


class PromptTemplate(PromptTemplateBase):
    template: str
    template_engine: PromptTemplatingEngine
    prompt_config: PromptTemplateConfig

    def __init__(
        self,
        template: str,
        template_engine: PromptTemplatingEngine,
        prompt_config: PromptTemplateConfig,
    ) -> None:
        super().__init__(
            template=template,
            template_engine=template_engine,
            prompt_config=prompt_config,
        )

    def get_parameters(self) -> List[KernelParameterMetadata]:
        seen = set()

        result = []
        for param in self.prompt_config.parameters:
            if param is None:
                continue

            result.append(
                KernelParameterMetadata(
                    name=param.name,
                    description=param.description,
                    default_value=param.default_value,
                    type_=param.type_,
                    required=param.required,
                )
            )

            seen.add(param.name)

        blocks = self.template_engine.extract_blocks(self.template)
        for block in blocks:
            if block.type != BlockTypes.VARIABLE:
                continue
            if block is None:
                continue

            var_block: VarBlock = block  # type: ignore
            if var_block.name in seen:
                continue

            result.append(KernelParameterMetadata(name=var_block.name, description="", default_value=""))

            seen.add(var_block.name)

        return result

    async def render(self, kernel: "Kernel", arguments: "KernelArguments") -> str:
        return await self.template_engine.render(self.template, kernel, arguments)
