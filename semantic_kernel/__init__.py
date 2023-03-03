# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.kernel_base import KernelBase
from semantic_kernel.kernel_builder import KernelBuilder
from semantic_kernel.kernel_extensions import KernelExtensions as extensions
from semantic_kernel.utils.settings import openai_settings_from_dot_env
from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.semantic_functions.semantic_function_config import (
    SemanticFunctionConfig,
)
from semantic_kernel.semantic_functions.prompt_template_config import (
    PromptTemplateConfig,
)
from semantic_kernel.semantic_functions.prompt_template import (
    PromptTemplate,
)



def create_kernel() -> KernelBase:
    return KernelBuilder.create_kernel()


__all__ = [
    "create_kernel",
    "openai_settings_from_dot_env",
    "extensions",
    "PromptTemplateConfig",
    "PromptTemplate",
    "SemanticFunctionConfig",
    "ContextVariables",
]
