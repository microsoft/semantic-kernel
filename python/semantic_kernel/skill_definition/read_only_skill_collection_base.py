# Copyright (c) Microsoft. All rights reserved.

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

from semantic_kernel.sk_pydantic import PydanticField

if TYPE_CHECKING:
    from semantic_kernel.orchestration.sk_function_base import SKFunctionBase
    from semantic_kernel.skill_definition.functions_view import FunctionsView


class ReadOnlySkillCollectionBase(PydanticField, ABC):
    @abstractmethod
    def has_function(self, skill_name: Optional[str], function_name: str) -> bool:
        pass

    @abstractmethod
    def has_semantic_function(
        self, skill_name: Optional[str], function_name: str
    ) -> bool:
        pass

    @abstractmethod
    def has_native_function(
        self, skill_name: Optional[str], function_name: str
    ) -> bool:
        pass

    @abstractmethod
    def get_semantic_function(
        self, skill_name: Optional[str], function_name: str
    ) -> "SKFunctionBase":
        pass

    @abstractmethod
    def get_native_function(
        self, skill_name: Optional[str], function_name: str
    ) -> "SKFunctionBase":
        pass

    @abstractmethod
    def get_functions_view(
        self, include_semantic: bool = True, include_native: bool = True
    ) -> "FunctionsView":
        pass

    @abstractmethod
    def get_function(
        self, skill_name: Optional[str], function_name: str
    ) -> "SKFunctionBase":
        pass
