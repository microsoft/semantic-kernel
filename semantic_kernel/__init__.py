# Copyright (c) Microsoft. All rights reserved.

import semantic_kernel.memory as memory
from semantic_kernel.configuration.kernel_config import KernelConfig
from semantic_kernel.kernel_base import KernelBase
from semantic_kernel.kernel_builder import KernelBuilder
from semantic_kernel.kernel_extensions import KernelExtensions as extensions
from semantic_kernel.memory.null_memory import NullMemory
from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.orchestration.sk_context import SKContext
from semantic_kernel.orchestration.sk_function_base import SKFunctionBase
from semantic_kernel.semantic_functions.prompt_template import PromptTemplate
from semantic_kernel.semantic_functions.prompt_template_config import (
    PromptTemplateConfig,
)
from semantic_kernel.semantic_functions.semantic_function_config import (
    SemanticFunctionConfig,
)
from semantic_kernel.utils.null_logger import NullLogger
from semantic_kernel.utils.settings import openai_settings_from_dot_env


def create_kernel() -> KernelBase:
    return KernelBuilder.create_kernel()


def kernel_builder() -> KernelBuilder:
    return KernelBuilder(KernelConfig(), NullMemory(), NullLogger())


__all__ = [
    "create_kernel",
    "openai_settings_from_dot_env",
    "extensions",
    "PromptTemplateConfig",
    "PromptTemplate",
    "SemanticFunctionConfig",
    "ContextVariables",
    "SKFunctionBase",
    "SKContext",
    "memory",
]
