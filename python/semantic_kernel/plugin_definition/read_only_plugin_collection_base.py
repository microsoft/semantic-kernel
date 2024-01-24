# Copyright (c) Microsoft. All rights reserved.

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional

from semantic_kernel.kernel_pydantic import KernelBaseModel

if TYPE_CHECKING:
    from semantic_kernel.orchestration.kernel_function_base import KernelFunctionBase
    from semantic_kernel.plugin_definition.functions_view import FunctionsView


class ReadOnlyPluginCollectionBase(KernelBaseModel, ABC):
    @abstractmethod
    def has_function(self, plugin_name: Optional[str], function_name: str) -> bool:
        pass

    @abstractmethod
    def has_semantic_function(self, plugin_name: Optional[str], function_name: str) -> bool:
        pass

    @abstractmethod
    def has_native_function(self, plugin_name: Optional[str], function_name: str) -> bool:
        pass

    @abstractmethod
    def get_semantic_function(self, plugin_name: Optional[str], function_name: str) -> "KernelFunctionBase":
        pass

    @abstractmethod
    def get_native_function(self, plugin_name: Optional[str], function_name: str) -> "KernelFunctionBase":
        pass

    @abstractmethod
    def get_functions_view(self, include_semantic: bool = True, include_native: bool = True) -> "FunctionsView":
        pass

    @abstractmethod
    def get_function(self, plugin_name: Optional[str], function_name: str) -> "KernelFunctionBase":
        pass
