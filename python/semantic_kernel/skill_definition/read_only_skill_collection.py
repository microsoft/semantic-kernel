# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import TYPE_CHECKING, Dict, Generic, Literal, Optional, Tuple, TypeVar

import pydantic as pdt

from semantic_kernel.kernel_exception import KernelException
from semantic_kernel.sk_pydantic import SKGenericModel
from semantic_kernel.skill_definition.functions_view import FunctionsView
from semantic_kernel.skill_definition.read_only_skill_collection_base import (
    ReadOnlySkillCollectionBase,
)
from semantic_kernel.utils.null_logger import NullLogger
from semantic_kernel.utils.static_property import static_property

if TYPE_CHECKING:
    from semantic_kernel.orchestration.sk_function_base import SKFunctionBase


SKFunctionT = TypeVar("SKFunctionT", bound="SKFunctionBase")


class ReadOnlySkillCollection(
    SKGenericModel, ReadOnlySkillCollectionBase, Generic[SKFunctionT]
):
    data: Dict[str, Dict[str, SKFunctionT]]
    _log: Logger = pdt.PrivateAttr()

    class Config:
        allow_mutation = False

    def __init__(
        self, data: Dict[str, Dict[str, SKFunctionT]], log: Optional[Logger] = None
    ) -> None:
        super().__init__(data=data)
        self._log = log or NullLogger()

    def has_function(self, skill_name: Optional[str], function_name: str) -> bool:
        s_name, f_name = self._normalize_names(skill_name, function_name, True)
        if s_name not in self.data:
            return False
        return f_name in self.data[s_name]

    def has_semantic_function(self, skill_name: str, function_name: str) -> bool:
        s_name, f_name = self._normalize_names(skill_name, function_name)
        if s_name not in self.data:
            return False
        if f_name not in self.data[s_name]:
            return False
        return self.data[s_name][f_name].is_semantic

    def has_native_function(self, skill_name: str, function_name: str) -> bool:
        s_name, f_name = self._normalize_names(skill_name, function_name, True)
        if s_name not in self.data:
            return False
        if f_name not in self.data[s_name]:
            return False
        return self.data[s_name][f_name].is_native

    def get_semantic_function(
        self, skill_name: str, function_name: str
    ) -> "SKFunctionBase":
        s_name, f_name = self._normalize_names(skill_name, function_name)
        if self.has_semantic_function(s_name, f_name):
            return self.data[s_name][f_name]

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
            return self.data[s_name][f_name]

        self._log.error(f"Function not available: {s_name}.{f_name}")
        raise KernelException(
            KernelException.ErrorCodes.FunctionNotAvailable,
            f"Function not available: {s_name}.{f_name}",
        )

    def get_functions_view(
        self, include_semantic: bool = True, include_native: bool = True
    ) -> FunctionsView:
        result = FunctionsView()

        for skill in self.data.values():
            for function in skill.values():
                if include_semantic and function.is_semantic:
                    result.add_function(function.describe())
                elif include_native and function.is_native:
                    result.add_function(function.describe())

        return result

    def get_function(
        self, skill_name: Optional[str], function_name: str
    ) -> "SKFunctionBase":
        s_name, f_name = self._normalize_names(skill_name, function_name, True)
        if self.has_function(s_name, f_name):
            return self.data[s_name][f_name]

        self._log.error(f"Function not available: {s_name}.{f_name}")
        raise KernelException(
            KernelException.ErrorCodes.FunctionNotAvailable,
            f"Function not available: {s_name}.{f_name}",
        )

    def _normalize_names(
        self,
        skill_name: Optional[str],
        function_name: str,
        allow_substitution: bool = False,
    ) -> Tuple[str, str]:
        s_name, f_name = skill_name, function_name
        if s_name is None and allow_substitution:
            s_name = self.GLOBAL_SKILL

        if s_name is None:
            raise ValueError("The skill name provided cannot be `None`")

        s_name, f_name = s_name.lower(), f_name.lower()
        return s_name, f_name

    @static_property
    def GLOBAL_SKILL() -> Literal["_GLOBAL_FUNCTIONS_"]:
        return "_GLOBAL_FUNCTIONS_"
