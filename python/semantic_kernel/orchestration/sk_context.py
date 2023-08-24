# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import Any, Generic, Literal, Optional, Tuple, Union

import pydantic as pdt

from semantic_kernel.kernel_exception import KernelException
from semantic_kernel.memory.semantic_text_memory_base import (
    SemanticTextMemoryBase,
    SemanticTextMemoryT,
)
from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.sk_pydantic import SKGenericModel
from semantic_kernel.skill_definition.read_only_skill_collection import (
    ReadOnlySkillCollection,
)
from semantic_kernel.skill_definition.read_only_skill_collection_base import (
    ReadOnlySkillCollectionBase,
)


class SKContext(SKGenericModel, Generic[SemanticTextMemoryT]):
    """Semantic Kernel context."""

    memory: SemanticTextMemoryT
    variables: ContextVariables
    skill_collection: ReadOnlySkillCollection = pdt.Field(
        default_factory=ReadOnlySkillCollection
    )
    _error_occurred: bool = pdt.PrivateAttr(False)
    _last_exception: Optional[Exception] = pdt.PrivateAttr(None)
    _last_error_description: str = pdt.PrivateAttr("")
    _logger: Logger = pdt.PrivateAttr()

    def __init__(
        self,
        variables: ContextVariables,
        memory: SemanticTextMemoryBase,
        skill_collection: Union[ReadOnlySkillCollection, None],
        logger: Optional[Logger] = None,
        # TODO: cancellation token?
    ) -> None:
        """
        Initializes a new instance of the SKContext class.

        Arguments:
            variables {ContextVariables} -- The context variables.
            memory {SemanticTextMemoryBase} -- The semantic text memory.
            skill_collection {ReadOnlySkillCollectionBase} -- The skill collection.
            logger {Logger} -- The logger.
        """
        # Local import to avoid circular dependency
        from semantic_kernel import NullLogger

        if skill_collection is None:
            skill_collection = ReadOnlySkillCollection()

        super().__init__(
            variables=variables, memory=memory, skill_collection=skill_collection
        )
        self._logger = logger or NullLogger()

    def fail(self, error_description: str, exception: Optional[Exception] = None):
        """
        Call this method to signal that an error occurred.
        In the usual scenarios, this is also how execution is stopped
        e.g., to inform the user or take necessary steps.

        Arguments:
            error_description {str} -- The error description.

        Keyword Arguments:
            exception {Exception} -- The exception (default: {None}).
        """
        self._error_occurred = True
        self._last_error_description = error_description
        self._last_exception = exception

    @property
    def result(self) -> str:
        """
        Print the processed input, aka the current data
        after any processing that has occurred.

        Returns:
            str -- Processed input, aka result.
        """
        return str(self.variables)

    @property
    def error_occurred(self) -> bool:
        """
        Whether an error occurred while executing functions in the pipeline.

        Returns:
            bool -- Whether an error occurred.
        """
        return self._error_occurred

    @property
    def last_error_description(self) -> str:
        """
        The last error description.

        Returns:
            str -- The last error description.
        """
        return self._last_error_description

    @property
    def last_exception(self) -> Optional[Exception]:
        """
        When an error occurs, this is the most recent exception.

        Returns:
            Exception -- The most recent exception.
        """
        return self._last_exception

    @property
    def skills(self) -> ReadOnlySkillCollectionBase:
        """
        Read only skills collection.

        Returns:
            ReadOnlySkillCollectionBase -- The skills collection.
        """
        return self.skill_collection

    @skills.setter
    def skills(self, value: ReadOnlySkillCollectionBase) -> None:
        """
        Set the value of skills collection
        """
        self.skill_collection = value

    @property
    def log(self) -> Logger:
        """
        The logger.

        Returns:
            Logger -- The logger.
        """
        return self._logger

    def __setitem__(self, key: str, value: Any) -> None:
        """
        Sets a context variable.

        Arguments:
            key {str} -- The variable name.
            value {Any} -- The variable value.
        """
        self.variables[key] = value

    def __getitem__(self, key: str) -> Any:
        """
        Gets a context variable.

        Arguments:
            key {str} -- The variable name.

        Returns:
            Any -- The variable value.
        """
        return self.variables[key]

    def func(self, skill_name: str, function_name: str):
        """
        Access registered functions by skill + name. Not case sensitive.
        The function might be native or semantic, it's up to the caller
        handling it.

        Arguments:
            skill_name {str} -- The skill name.
            function_name {str} -- The function name.

        Returns:
            SKFunctionBase -- The function.
        """
        if self.skill_collection is None:
            raise ValueError("The skill collection hasn't been set")
        assert self.skill_collection is not None  # for type checker

        if self.skill_collection.has_native_function(skill_name, function_name):
            return self.skill_collection.get_native_function(skill_name, function_name)

        return self.skill_collection.get_semantic_function(skill_name, function_name)

    def __str__(self) -> str:
        if self._error_occurred:
            return f"Error: {self._last_error_description}"

        return self.result

    def throw_if_skill_collection_not_set(self) -> None:
        """
        Throws an exception if the skill collection hasn't been set.
        """
        if self.skill_collection is None:
            raise KernelException(
                KernelException.ErrorCodes.SkillCollectionNotSet,
                "Skill collection not found in the context",
            )

    def is_function_registered(
        self, skill_name: str, function_name: str
    ) -> Union[Tuple[Literal[True], Any], Tuple[Literal[False], None]]:
        """
        Checks whether a function is registered in this context.

        Arguments:
            skill_name {str} -- The skill name.
            function_name {str} -- The function name.

        Returns:
            Tuple[bool, SKFunctionBase] -- A tuple with a boolean indicating
            whether the function is registered and the function itself (or None).
        """
        self.throw_if_skill_collection_not_set()
        assert self.skill_collection is not None  # for type checker

        if self.skill_collection.has_native_function(skill_name, function_name):
            the_func = self.skill_collection.get_native_function(
                skill_name, function_name
            )
            return True, the_func

        if self.skill_collection.has_native_function(None, function_name):
            the_func = self.skill_collection.get_native_function(None, function_name)
            return True, the_func

        if self.skill_collection.has_semantic_function(skill_name, function_name):
            the_func = self.skill_collection.get_semantic_function(
                skill_name, function_name
            )
            return True, the_func

        return False, None
