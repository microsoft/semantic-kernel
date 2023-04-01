# Copyright (c) Microsoft. All rights reserved.

from typing import TYPE_CHECKING, Optional

from semantic_kernel.skill_definition.read_only_skill_collection_base import (
    ReadOnlySkillCollectionBase,
)

if TYPE_CHECKING:
    from semantic_kernel.orchestration.sk_function_base import SKFunctionBase
    from semantic_kernel.skill_definition.functions_view import FunctionsView
    from semantic_kernel.skill_definition.skill_collection_base import (
        SkillCollectionBase,
    )


class ReadOnlySkillCollection(ReadOnlySkillCollectionBase):
    _skill_collection: "SkillCollectionBase"

    def __init__(self, skill_collection: "SkillCollectionBase") -> None:
        self._skill_collection = skill_collection

    def has_function(self, skill_name: Optional[str], function_name: str) -> bool:
        return self._skill_collection.has_function(skill_name, function_name)

    def has_semantic_function(
        self, skill_name: Optional[str], function_name: str
    ) -> bool:
        return self._skill_collection.has_semantic_function(skill_name, function_name)

    def has_native_function(
        self, skill_name: Optional[str], function_name: str
    ) -> bool:
        return self._skill_collection.has_native_function(skill_name, function_name)

    def get_semantic_function(
        self, skill_name: Optional[str], function_name: str
    ) -> "SKFunctionBase":
        return self._skill_collection.get_semantic_function(skill_name, function_name)

    def get_native_function(
        self, skill_name: Optional[str], function_name: str
    ) -> "SKFunctionBase":
        return self._skill_collection.get_native_function(skill_name, function_name)

    def get_functions_view(
        self, include_semantic: bool = True, include_native: bool = True
    ) -> "FunctionsView":
        return self._skill_collection.get_functions_view(
            include_semantic, include_native
        )

    def get_function(
        self, skill_name: Optional[str], function_name: str
    ) -> "SKFunctionBase":
        return self._skill_collection.get_function(skill_name, function_name)
