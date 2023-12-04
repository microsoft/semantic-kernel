# Copyright (c) Microsoft. All rights reserved.

from dataclasses import dataclass
from typing import TYPE_CHECKING

from semantic_kernel.semantic_functions.chat_prompt_template import ChatPromptTemplate

if TYPE_CHECKING:
    from semantic_kernel.semantic_functions.prompt_config import (
        PromptConfig,
    )
    from semantic_kernel.semantic_functions.prompt_template import PromptTemplate


@dataclass
class SemanticFunctionConfig:
    prompt_template_config: "PromptConfig"
    prompt_template: "PromptTemplate"

    @property
    def has_chat_prompt(self) -> bool:
        return isinstance(self.prompt_template, ChatPromptTemplate)
