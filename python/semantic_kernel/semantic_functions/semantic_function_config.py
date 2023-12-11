# Copyright (c) Microsoft. All rights reserved.

from dataclasses import dataclass
from typing import TYPE_CHECKING

from semantic_kernel.semantic_functions.chat_prompt_template import ChatPromptTemplate

if TYPE_CHECKING:
    from semantic_kernel.semantic_functions.prompt_template import PromptTemplate
    from semantic_kernel.semantic_functions.prompt_template_config import (
        PromptTemplateConfig,
    )


@dataclass
class SemanticFunctionConfig:
    prompt_template_config: "PromptTemplateConfig"
    prompt_template: "PromptTemplate"

    @property
    def has_chat_prompt(self) -> bool:
        return isinstance(self.prompt_template, ChatPromptTemplate)
