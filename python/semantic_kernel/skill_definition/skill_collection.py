# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import TYPE_CHECKING, Dict, Literal, Optional, Tuple

from semantic_kernel.diagnostics.verify import Verify
from semantic_kernel.kernel_exception import KernelException
from semantic_kernel.skill_definition.functions_view import FunctionsView
from semantic_kernel.skill_definition.read_only_skill_collection import (
    ReadOnlySkillCollection,
)
from semantic_kernel.skill_definition.skill_collection_base import SkillCollectionBase
from semantic_kernel.utils.null_logger import NullLogger
from semantic_kernel.utils.static_property import static_property

if TYPE_CHECKING:
    from semantic_kernel.orchestration.sk_function_base import SKFunctionBase
    from semantic_kernel.skill_definition.read_only_skill_collection_base import (
        ReadOnlySkillCollectionBase,
    )


class SkillCollection(SkillCollectionBase):
    _skill_collection: Dict[str, Dict[str, "SKFunctionBase"]]
    _read_only_skill_collection: "ReadOnlySkillCollectionBase"
    _log: Logger

    @property
    def read_only_skill_collection(self) -> "ReadOnlySkillCollectionBase":
        return self._read_only_skill_collection

    def __init__(self, log: Optional[Logger] = None) -> None:
        self._log = log if log is not None else NullLogger()
        self._read_only_skill_collection = ReadOnlySkillCollection(self)
        self._skill_collection = {}

    def add_semantic_function(self, function: "SKFunctionBase") -> None:
        Verify.not_null(function, "The function provided is None")

        s_name, f_name = function.skill_name, function.name
        s_name, f_name = s_name.lower(), f_name.lower()

        if s_name not in self._skill_collection:
            self._skill_collection[s_name] = {}

        self._skill_collection[s_name][f_name] = function

    def add_native_function(self, function: "SKFunctionBase") -> None:
        Verify.not_null(function, "The function provided is None")

        s_name, f_name = function.skill_name, function.name
        s_name, f_name = self._normalize_names(s_name, f_name, True)

        if s_name not in self._skill_collection:
            self._skill_collection[s_name] = {}

        self._skill_collection[s_name][f_name] = function

    def has_function(self, skill_name: Optional[str], function_name: str) -> bool:
        s_name, f_name = self._normalize_names(skill_name, function_name, True)
        if s_name not in self._skill_collection:
            return False
        return f_name in self._skill_collection[s_name]

    def has_semantic_function(self, skill_name: str, function_name: str) -> bool:
        s_name, f_name = self._normalize_names(skill_name, function_name)
        if s_name not in self._skill_collection:
            return False
        if f_name not in self._skill_collection[s_name]:
            return False
        return self._skill_collection[s_name][f_name].is_semantic

    def has_native_function(self, skill_name: str, function_name: str) -> bool:
        s_name, f_name = self._normalize_names(skill_name, function_name, True)
        if s_name not in self._skill_collection:
            return False
        if f_name not in self._skill_collection[s_name]:
            return False
        return self._skill_collection[s_name][f_name].is_native

    def get_semantic_function(
        self, skill_name: str, function_name: str
    ) -> "SKFunctionBase":
        s_name, f_name = self._normalize_names(skill_name, function_name)
        if self.has_semantic_function(s_name, f_name):
            return self._skill_collection[s_name][f_name]

        self._log.error(f"Function not available: {s_name}.{f_name}")
        raise KernelException(
            KernelException.ErrorCodes.FunctionNotAvailable,
            f"Function not available: {s_name}.{f_name}",
        )

    def get_native_function(
        self, skill_name: str, function_name: str
    ) -> "SKFunctionBase":
        s_name, f_name = self._normalize_names(skill_name, function_name, True)
        if self.has_native_function(s_name, f_name):
            return self._skill_collection[s_name][f_name]

        self._log.error(f"Function not available: {s_name}.{f_name}")
        raise KernelException(
            KernelException.ErrorCodes.FunctionNotAvailable,
            f"Function not available: {s_name}.{f_name}",
        )

    def get_functions_view(
        self, include_semantic: bool = True, include_native: bool = True
    ) -> FunctionsView:
        result = FunctionsView()

        for skill in self._skill_collection.values():
            for function in skill.values():
                if include_semantic and function.is_semantic:
                    result.add_function(function.describe())
                elif include_native and function.is_native:
                    result.add_function(function.describe())

        return result

    def _normalize_names(
        self,
        skill_name: Optional[str],
        function_name: str,
        allow_substitution: bool = False,
    ) -> Tuple[str, str]:
        s_name, f_name = skill_name, function_name
        if s_name is None and allow_substitution:
            s_name = self.GLOBAL_SKILL

        Verify.not_null(s_name, "The skill name provided is None")
        assert s_name is not None  # to make type checker happy

        s_name, f_name = s_name.lower(), f_name.lower()
        return s_name, f_name

    @static_property
    def GLOBAL_SKILL() -> Literal["_GLOBAL_FUNCTIONS_"]:
        return "_GLOBAL_FUNCTIONS_"
