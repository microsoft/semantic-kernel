# Copyright (c) Microsoft. All rights reserved.

from abc import abstractmethod
from logging import Logger
from typing import TYPE_CHECKING, Callable, Optional

from semantic_kernel.connectors.ai.complete_request_settings import (
    CompleteRequestSettings,
)
from semantic_kernel.connectors.ai.text_completion_client_base import (
    TextCompletionClientBase,
)
from semantic_kernel.memory.semantic_text_memory_base import SemanticTextMemoryBase
from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.sk_pydantic import PydanticField
from semantic_kernel.skill_definition.function_view import FunctionView

if TYPE_CHECKING:
    from semantic_kernel.orchestration.sk_context import SKContext
    from semantic_kernel.skill_definition.read_only_skill_collection_base import (
        ReadOnlySkillCollectionBase,
    )


class SKFunctionBase(PydanticField):
    FUNCTION_PARAM_NAME_REGEX = r"^[0-9A-Za-z_]*$"
    FUNCTION_NAME_REGEX = r"^[0-9A-Za-z_]*$"
    SKILL_NAME_REGEX = r"^[0-9A-Za-z_]*$"

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
    def invoke(
        self,
        input: Optional[str] = None,
        variables: ContextVariables = None,
        context: Optional["SKContext"] = None,
        memory: Optional[SemanticTextMemoryBase] = None,
        settings: Optional[CompleteRequestSettings] = None,
        log: Optional[Logger] = None,
    ) -> "SKContext":
        """
        Invokes the function with an explicit string input
        Keyword Arguments:
            input {str} -- The explicit string input (default: {None})
            variables {ContextVariables} -- The custom input
            context {SKContext} -- The context to use
            memory: {SemanticTextMemoryBase} -- The memory to use
            settings {CompleteRequestSettings} -- LLM completion settings
            log {Logger} -- Application logger
        Returns:
            SKContext -- The updated context, potentially a new one if
            context switching is implemented.
        """
        pass

    @abstractmethod
    async def invoke_async(
        self,
        input: Optional[str] = None,
        variables: ContextVariables = None,
        context: Optional["SKContext"] = None,
        memory: Optional[SemanticTextMemoryBase] = None,
        settings: Optional[CompleteRequestSettings] = None,
        log: Optional[Logger] = None,
    ) -> "SKContext":
        """
        Invokes the function with an explicit string input
        Keyword Arguments:
            input {str} -- The explicit string input (default: {None})
            variables {ContextVariables} -- The custom input
            context {SKContext} -- The context to use
            memory: {SemanticTextMemoryBase} -- The memory to use
            settings {CompleteRequestSettings} -- LLM completion settings
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
    def set_ai_service(
        self, service_factory: Callable[[], TextCompletionClientBase]
    ) -> "SKFunctionBase":
        """
        Sets the AI service used by the semantic function, passing in a factory
        method. The factory allows us to lazily instantiate the client and to
        properly handle its disposal

        Arguments:
            service_factory -- AI service factory

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
