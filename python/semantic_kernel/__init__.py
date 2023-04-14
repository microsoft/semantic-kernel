# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel import core_skills, memory
from semantic_kernel.kernel import Kernel
from semantic_kernel.kernel_builder import KernelBuilder
from semantic_kernel.kernel_config import KernelConfig
from semantic_kernel.memory.null_memory import NullMemory
from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.orchestration.sk_context import SKContext
from semantic_kernel.orchestration.sk_function_base import SKFunctionBase
from semantic_kernel.semantic_functions.chat_prompt_template import ChatPromptTemplate
from semantic_kernel.semantic_functions.prompt_template import PromptTemplate
from semantic_kernel.semantic_functions.prompt_template_config import (
    PromptTemplateConfig,
)
from semantic_kernel.semantic_functions.semantic_function_config import (
    SemanticFunctionConfig,
)
from semantic_kernel.utils.null_logger import NullLogger
from semantic_kernel.utils.settings import (
    azure_openai_settings_from_dot_env,
    openai_settings_from_dot_env,
)


def create_kernel() -> Kernel:
    return KernelBuilder.create_kernel()


def kernel_builder() -> KernelBuilder:
    return KernelBuilder(KernelConfig(), NullMemory(), NullLogger())


__all__ = [
    "create_kernel",
    "openai_settings_from_dot_env",
    "azure_openai_settings_from_dot_env",
    "PromptTemplateConfig",
    "PromptTemplate",
    "ChatPromptTemplate",
    "SemanticFunctionConfig",
    "ContextVariables",
    "SKFunctionBase",
    "SKContext",
    "memory",
    "core_skills",
]
