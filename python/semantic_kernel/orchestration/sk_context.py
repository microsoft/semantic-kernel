# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import Any, Literal, Optional, Tuple, Union

from semantic_kernel.diagnostics.verify import Verify
from semantic_kernel.kernel_exception import KernelException
from semantic_kernel.memory.semantic_text_memory_base import SemanticTextMemoryBase
from semantic_kernel.orchestration.context_variables import ContextVariables
from semantic_kernel.skill_definition.read_only_skill_collection_base import (
    ReadOnlySkillCollectionBase,
)


class SKContext:
    """Semantic Kernel context."""

    _error_occurred: bool = False
    _last_exception: Optional[Exception] = None
    _last_error_description: str = ""
    _logger: Logger
    _memory: SemanticTextMemoryBase
    _skill_collection: ReadOnlySkillCollectionBase
    _variables: ContextVariables

    def __init__(
        self,
        variables: ContextVariables,
        memory: SemanticTextMemoryBase,
        skill_collection: ReadOnlySkillCollectionBase,
        logger: Logger,
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
        self._variables = variables
        self._memory = memory
        self._skill_collection = skill_collection
        self._logger = logger

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
        return str(self._variables)

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
    def variables(self) -> ContextVariables:
        """
        User variables.

        Returns:
            ContextVariables -- The context variables.
        """
        return self._variables

    @property
    def memory(self) -> SemanticTextMemoryBase:
        """
        The semantic text memory.

        Returns:
            SemanticTextMemoryBase -- The semantic text memory.
        """
        return self._memory

    @property
    def skills(self) -> ReadOnlySkillCollectionBase:
        """
        Read only skills collection.

        Returns:
            ReadOnlySkillCollectionBase -- The skills collection.
        """
        return self._skill_collection

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
        self._variables[key] = value

    def __getitem__(self, key: str) -> Any:
        """
        Gets a context variable.

        Arguments:
            key {str} -- The variable name.

        Returns:
            Any -- The variable value.
        """
        return self._variables[key]

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
        Verify.not_null(self._skill_collection, "The skill collection hasn't been set")
        assert self._skill_collection is not None  # for type checker

        if self._skill_collection.has_native_function(skill_name, function_name):
            return self._skill_collection.get_native_function(skill_name, function_name)

        return self._skill_collection.get_semantic_function(skill_name, function_name)

    def __str__(self) -> str:
        if self._error_occurred:
            return f"Error: {self._last_error_description}"

        return self.result

    def throw_if_skill_collection_not_set(self) -> None:
        """
        Throws an exception if the skill collection hasn't been set.
        """
        if self._skill_collection is None:
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
        assert self._skill_collection is not None  # for type checker

        if self._skill_collection.has_native_function(skill_name, function_name):
            the_func = self._skill_collection.get_native_function(
                skill_name, function_name
            )
            return True, the_func

        if self._skill_collection.has_native_function(None, function_name):
            the_func = self._skill_collection.get_native_function(None, function_name)
            return True, the_func

        if self._skill_collection.has_semantic_function(skill_name, function_name):
            the_func = self._skill_collection.get_semantic_function(
                skill_name, function_name
            )
            return True, the_func

        return False, None
