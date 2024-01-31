# Copyright (c) Microsoft. All rights reserved.

from abc import abstractmethod
from typing import TYPE_CHECKING, Any, Callable, Dict, Optional

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.connectors.ai.text_completion_client_base import (
    TextCompletionClientBase,
)
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.memory.semantic_text_memory_base import SemanticTextMemoryBase
from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.plugin_definition.function_view import FunctionView

if TYPE_CHECKING:
    from semantic_kernel.orchestration.kernel_context import KernelContext
    from semantic_kernel.plugin_definition.read_only_plugin_collection_base import (
        ReadOnlyPluginCollectionBase,
    )


class KernelFunctionBase(KernelBaseModel):
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Name of the function.

        The name is used by the plugin collection and in
        prompt templates; e.g., {{pluginName.functionName}}
        """
        pass

    @property
    @abstractmethod
    def plugin_name(self) -> str:
        """
        Name of the plugin that contains this function.

        The name is used by the plugin collection and in
        prompt templates; e.g., {{pluginName.functionName}}"""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """
        Function description.

        The description is used in combination with embeddings
        when searching for relevant functions."""
        pass

    @property
    @abstractmethod
    def is_semantic(self) -> bool:
        """
        Whether the function is semantic.

        IMPORTANT: native functions might use semantic functions
        internally, so when this property is False, executing
        the function might still involve AI calls.
        """
        pass

    @property
    @abstractmethod
    def is_native(self) -> bool:
        """
        Whether the function is native.

        IMPORTANT: native functions might use semantic functions
        internally, so when this property is True, executing
        the function might still involve AI calls.
        """
        pass

    @property
    @abstractmethod
    def prompt_execution_settings(self) -> PromptExecutionSettings:
        """AI service settings"""
        pass

    @abstractmethod
    def describe() -> FunctionView:
        """
        Returns a description of the function,
        including its parameters

        Returns:
            FunctionView -- The function description.
        """
        pass

    @abstractmethod
    async def invoke(
        self,
        input: Optional[str] = None,
        variables: ContextVariables = None,
        context: Optional["KernelContext"] = None,
        memory: Optional[SemanticTextMemoryBase] = None,
        settings: Optional[PromptExecutionSettings] = None,
        **kwargs: Dict[str, Any],
    ) -> "KernelContext":
        """
        Invokes the function with an explicit string input
        Keyword Arguments:
            input {str} -- The explicit string input (default: {None})
            variables {ContextVariables} -- The custom input
            context {KernelContext} -- The context to use
            memory: {SemanticTextMemoryBase} -- The memory to use
            settings {PromptExecutionSettings} -- LLM completion settings
        Returns:
            KernelContext -- The updated context, potentially a new one if
            context switching is implemented.
        """
        pass

    @abstractmethod
    def set_default_plugin_collection(
        self,
        plugins: "ReadOnlyPluginCollectionBase",
    ) -> "KernelFunctionBase":
        """
        Sets the plugin collection to use when the function is
        invoked without a context or with a context that doesn't have
        a plugin collection

        Arguments:
            plugins {ReadOnlyPluginCollectionBase} -- Kernel's plugin collection

        Returns:
            KernelFunctionBase -- The function instance
        """
        pass

    @abstractmethod
    def set_ai_service(self, service_factory: Callable[[], TextCompletionClientBase]) -> "KernelFunctionBase":
        """
        Sets the AI service used by the semantic function, passing in a factory
        method. The factory allows us to lazily instantiate the client and to
        properly handle its disposal

        Arguments:
            service_factory -- AI service factory

        Returns:
            KernelFunctionBase -- The function instance
        """
        pass

    @abstractmethod
    def set_ai_configuration(self, settings: PromptExecutionSettings) -> "KernelFunctionBase":
        """
        Sets the AI completion settings used with LLM requests

        Arguments:
            settings {PromptExecutionSettings} -- LLM completion settings

        Returns:
            KernelFunctionBase -- The function instance
        """
        pass
