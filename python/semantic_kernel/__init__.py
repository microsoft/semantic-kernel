# Copyright (c) Microsoft. All rights reserved.

from pathlib import Path

from semantic_kernel import core_skills, memory
from semantic_kernel.kernel import Kernel
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
from semantic_kernel.settings import (
    KernelSettings,
    OpenAISettings,
    load_settings,
)
from semantic_kernel.utils.null_logger import NullLogger
from semantic_kernel.utils.settings import (
    azure_openai_settings_from_dot_env,
)

# Path to the `python` directory
PYTHON_REPO_ROOT = Path(__file__).parent.parent

__all__ = [
    "Kernel",
    "NullLogger",
    "KernelSettings",
    "OpenAISettings",
    "load_settings",
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
    "PYTHON_REPO_ROOT",
]
