# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import TYPE_CHECKING, ClassVar, Dict, List, Optional, Tuple

import pydantic as pdt

from semantic_kernel.kernel_exception import KernelException
from semantic_kernel.orchestration.sk_function import SKFunction
from semantic_kernel.sk_pydantic import SKBaseModel
from semantic_kernel.skill_definition import constants
from semantic_kernel.skill_definition.functions_view import FunctionsView
from semantic_kernel.skill_definition.read_only_skill_collection_base import (
    ReadOnlySkillCollectionBase,
)
from semantic_kernel.utils.null_logger import NullLogger

if TYPE_CHECKING:
    from semantic_kernel.orchestration.sk_function_base import SKFunctionBase


class ReadOnlySkillCollection(SKBaseModel, ReadOnlySkillCollectionBase):
    GLOBAL_SKILL: ClassVar[str] = constants.GLOBAL_SKILL
    data: Dict[str, Dict[str, SKFunction]] = pdt.Field(default_factory=dict)
    _log: Logger = pdt.PrivateAttr()

    class Config:
        allow_mutation = False

    def __init__(
        self,
        data: Dict[str, Dict[str, SKFunction]] = None,
        log: Optional[Logger] = None,
    ) -> None:
        super().__init__(data=data or {})
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

    # def has_callable_function(self, skill_name: str, function_name: str) -> bool:
    #     s_name, f_name = self._normalize_names(skill_name, function_name, True)
    #     if s_name not in self.data:
    #         return False
    #     if f_name not in self.data[s_name]:
    #         return False
    #     return self.data[s_name][f_name].function_calling_enabled

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

    # def get_callable_function(
    #     self, skill_name: str, function_name: str
    # ) -> "SKFunctionBase":
    #     s_name, f_name = self._normalize_names(skill_name, function_name, True)
    #     if self.has_callable_function(s_name, f_name):
    #         return self.data[s_name][f_name]

    #     self._log.error(f"Function not available: {s_name}.{f_name}")
    #     raise KernelException(
    #         KernelException.ErrorCodes.FunctionNotAvailable,
    #         f"Function not available: {s_name}.{f_name}",
    #     )

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

    def get_function_calling_object(
        self, filter: Dict[str, List[str]], caller_function_name: str
    ) -> List[Dict[str, str]]:
        """Create the object used for function_calling.

        args:
            filter: a dictionary with keys
                exclude_skill, include_skill, exclude_function, include_function
                and lists of the required filter.
                The function name should be in the format "skill_name-function_name".
                Using exclude_skill and include_skill at the same time will raise an error.
                Using exclude_function and include_function at the same time will raise an error.
                If using include_* implies that all other function will be excluded.
                Example:
                    filter = {
                        "exclude_skill": ["skill1", "skill2"],
                        "include_function": ["skill3-function1", "skill4-function2"],
                        }
                    will return only skill3-function1 and skill4-function2.
                    filter = {
                        "exclude_function": ["skill1-function1", "skill2-function2"],
                        }
                    will return all functions except skill1-function1 and skill2-function2.
            caller_function_name: the name of the function that is calling the other functions.
        returns:
            a list of dictionaries with keys that can be passed to the function calling api.
        """
        include_skill = filter.get("include_skill", None)
        exclude_skill = filter.get("exclude_skill", [])
        include_function = filter.get("include_function", None)
        exclude_function = filter.get("exclude_function", [])
        if include_skill and exclude_skill:
            raise ValueError(
                "Cannot use both include_skill and exclude_skill at the same time."
            )
        if include_function and exclude_function:
            raise ValueError(
                "Cannot use both include_function and exclude_function at the same time."
            )
        if include_skill:
            include_skill = [skill.lower() for skill in include_skill]
        if exclude_skill:
            exclude_skill = [skill.lower() for skill in exclude_skill]
        if include_function:
            include_function = [function.lower() for function in include_function]
        if exclude_function:
            exclude_function = [function.lower() for function in exclude_function]
        result = []
        for skill_name, skill in self.data.items():
            if skill_name in exclude_skill or (
                include_skill and skill_name not in include_skill
            ):
                continue
            for function_name, function in skill.items():
                current_name = f"{skill_name}-{function_name}"
                if (
                    current_name == caller_function_name.lower()
                    or current_name in exclude_function
                    or (include_function and current_name not in include_function)
                ):
                    continue
                result.append(function._function_calling_description)
        return result
