# Copyright (c) Microsoft. All rights reserved.

from logging import Logger
from typing import (
    TYPE_CHECKING,
    Dict,
    Generic,
    Optional,
    TypeVar,
    Union,
)

import pydantic as pdt

from semantic_kernel.sk_pydantic import SKGenericModel
from semantic_kernel.skill_definition.functions_view import FunctionsView
from semantic_kernel.skill_definition.read_only_skill_collection import (
    ReadOnlySkillCollection,
)
from semantic_kernel.skill_definition.read_only_skill_collection_base import (
    ReadOnlySkillCollectionBase,
)
from semantic_kernel.skill_definition.skill_collection_base import SkillCollectionBase
from semantic_kernel.utils.null_logger import NullLogger
from semantic_kernel.utils.static_property import static_property

if TYPE_CHECKING:
    from semantic_kernel.orchestration.sk_function_base import SKFunctionBase

SKFunctionT = TypeVar("SKFunctionT", bound="SKFunctionBase")


class SkillCollection(SKGenericModel, SkillCollectionBase, Generic[SKFunctionT]):
    read_only_skill_collection_: ReadOnlySkillCollection = pdt.Field(
        alias="read_only_skill_collection"
    )
    _log: Logger = pdt.PrivateAttr()

    def __init__(
        self,
        log: Optional[Logger] = None,
        skill_collection: Union[Dict[str, Dict[str, SKFunctionT]], None] = None,
        read_only_skill_collection_: Optional[ReadOnlySkillCollection] = None,
    ) -> None:
        if skill_collection and read_only_skill_collection_:
            raise ValueError(
                "Only one of `skill_collection` and `read_only_skill_collection` can be"
                " provided"
            )
        elif not skill_collection and not read_only_skill_collection_:
            read_only_skill_collection = ReadOnlySkillCollection({})
        elif not read_only_skill_collection_:
            read_only_skill_collection = ReadOnlySkillCollection(skill_collection)
        else:
            read_only_skill_collection = read_only_skill_collection_
        super().__init__(read_only_skill_collection=read_only_skill_collection)
        self._log = log if log is not None else NullLogger()

    @property
    def read_only_skill_collection(self) -> ReadOnlySkillCollectionBase:
        return self.read_only_skill_collection_

    @property
    def skill_collection(self):
        return self.read_only_skill_collection_.data

    def add_semantic_function(self, function: "SKFunctionBase") -> None:
        if function is None:
            raise ValueError("The function provided cannot be `None`")

        s_name, f_name = function.skill_name, function.name
        s_name, f_name = s_name.lower(), f_name.lower()

        if s_name not in self.skill_collection:
            self.skill_collection[s_name] = {}

        self.skill_collection[s_name][f_name] = function

    def add_native_function(self, function: "SKFunctionBase") -> None:
        if function is None:
            raise ValueError("The function provided cannot be `None`")

        s_name, f_name = function.skill_name, function.name
        s_name, f_name = self.read_only_skill_collection_._normalize_names(
            s_name, f_name, True
        )
        if s_name not in self.skill_collection:
            self.skill_collection[s_name] = {}

        self.skill_collection[s_name][f_name] = function

    def has_function(self, skill_name: Optional[str], function_name: str) -> bool:
        return self.read_only_skill_collection_.has_function(skill_name, function_name)

    def has_semantic_function(
        self, skill_name: Optional[str], function_name: str
    ) -> bool:
        return self.read_only_skill_collection_.has_semantic_function(
            skill_name, function_name
        )

    def has_native_function(
        self, skill_name: Optional[str], function_name: str
    ) -> bool:
        return self.read_only_skill_collection_.has_native_function(
            skill_name, function_name
        )

    def get_semantic_function(
        self, skill_name: Optional[str], function_name: str
    ) -> "SKFunctionBase":
        return self.read_only_skill_collection_.get_semantic_function(
            skill_name, function_name
        )

    def get_native_function(
        self, skill_name: Optional[str], function_name: str
    ) -> "SKFunctionBase":
        return self.read_only_skill_collection_.get_native_function(
            skill_name, function_name
        )

    def get_functions_view(
        self, include_semantic: bool = True, include_native: bool = True
    ) -> FunctionsView:
        return self.read_only_skill_collection_.get_functions_view(
            include_semantic, include_native
        )

    def get_function(
        self, skill_name: Optional[str], function_name: str
    ) -> "SKFunctionBase":
        return self.read_only_skill_collection_.get_function(skill_name, function_name)

    @static_property
    def GLOBAL_SKILL():
        return ReadOnlySkillCollection.GLOBAL_SKILL
