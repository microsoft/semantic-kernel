# Copyright (c) Microsoft. All rights reserved.

from abc import ABC, abstractmethod
from logging import Logger
from typing import TYPE_CHECKING, Callable, Optional

from semantic_kernel.ai.complete_request_settings import CompleteRequestSettings
from semantic_kernel.ai.text_completion_client_base import TextCompletionClientBase
from semantic_kernel.memory.semantic_text_memory_base import SemanticTextMemoryBase
from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.orchestration.sk_context import SKContext
from semantic_kernel.skill_definition.function_view import FunctionView

if TYPE_CHECKING:
    from semantic_kernel.skill_definition.read_only_skill_collection_base import (
        ReadOnlySkillCollectionBase,
    )


class SKFunctionBase(ABC):
    @property
    @abstractmethod
    def name(self) -> str:
        """
        Name of the function.

        The name is used by the skill collection and in
        prompt templates; e.g., {{skillName.functionName}}
        """
        pass

    @property
    @abstractmethod
    def skill_name(self) -> str:
        """
        Name of the skill that contains this function.

        The name is used by the skill collection and in
        prompt templates; e.g., {{skillName.functionName}}"""
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
    def request_settings(self) -> CompleteRequestSettings:
        """AI backend settings"""
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
    async def invoke_async(
        self,
        input: Optional[str] = None,
        context: Optional[SKContext] = None,
        settings: Optional[CompleteRequestSettings] = None,
        log: Optional[Logger] = None
        # TODO: ctoken
    ) -> SKContext:
        """
        Invokes the function with an explicit string input

        Keyword Arguments:
            input {str} -- The explicit string input (default: {None})
            context {SKContext} -- The context to use
            settings {CompleteRequestSettings} -- LLM completion settings
            log {Logger} -- Application logger

        Returns:
            SKContext -- The updated context, potentially a new one if
            context switching is implemented.
        """
        pass

    @abstractmethod
    async def invoke_with_custom_input_async(
        self,
        input: ContextVariables,
        memory: SemanticTextMemoryBase,
        skills: "ReadOnlySkillCollectionBase",
        log: Optional[Logger] = None,
    ) -> SKContext:
        """
        Invokes the function with a custom input

        Arguments:
            input {ContextVariables} -- The custom input
            memory {SemanticTextMemoryBase} -- The memory to use
            skills {ReadOnlySkillCollectionBase} -- The skill collection to use
            log {Logger} -- Application logger

        Returns:
            SKContext -- The updated context, potentially a new one if
            context switching is implemented.
        """
        pass

    @abstractmethod
    def set_default_skill_collection(
        self,
        skills: "ReadOnlySkillCollectionBase",
    ) -> "SKFunctionBase":
        """
        Sets the skill collection to use when the function is
        invoked without a context or with a context that doesn't have
        a skill collection

        Arguments:
            skills {ReadOnlySkillCollectionBase} -- Kernel's skill collection

        Returns:
            SKFunctionBase -- The function instance
        """
        pass

    @abstractmethod
    def set_ai_backend(
        self, backend_factory: Callable[[], TextCompletionClientBase]
    ) -> "SKFunctionBase":
        """
        Sets the AI backend used by the semantic function, passing in a factory
        method. The factory allows us to lazily instantiate the client and to
        properly handle its disposal

        Arguments:
            backend_factory -- AI backend factory

        Returns:
            SKFunctionBase -- The function instance
        """
        pass

    @abstractmethod
    def set_ai_configuration(
        self, settings: CompleteRequestSettings
    ) -> "SKFunctionBase":
        """
        Sets the AI completion settings used with LLM requests

        Arguments:
            settings {CompleteRequestSettings} -- LLM completion settings

        Returns:
            SKFunctionBase -- The function instance
        """
        pass
