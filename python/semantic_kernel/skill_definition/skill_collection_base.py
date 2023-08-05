# Copyright (c) Microsoft. All rights reserved.

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, TypeVar

from semantic_kernel.sk_pydantic import PydanticField
from semantic_kernel.skill_definition.read_only_skill_collection_base import (
    ReadOnlySkillCollectionBase,
)

if TYPE_CHECKING:
    from semantic_kernel.orchestration.sk_function_base import SKFunctionBase


SkillCollectionT = TypeVar("SkillCollectionT", bound="SkillCollectionBase")


class SkillCollectionBase(ReadOnlySkillCollectionBase, PydanticField, ABC):
    @property
    @abstractmethod
    def read_only_skill_collection(self) -> ReadOnlySkillCollectionBase:
        pass

    @abstractmethod
    def add_semantic_function(
        self, semantic_function: "SKFunctionBase"
    ) -> "SkillCollectionBase":
        pass

    @abstractmethod
    def add_native_function(
        self, native_function: "SKFunctionBase"
    ) -> "SkillCollectionBase":
        pass
