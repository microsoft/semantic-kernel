# Copyright (c) Microsoft. All rights reserved.

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, TypeVar

from semantic_kernel.plugin_definition.read_only_plugin_collection_base import (
    ReadOnlyPluginCollectionBase,
)

if TYPE_CHECKING:
    from semantic_kernel.orchestration.kernel_function_base import KernelFunctionBase


PluginCollectionT = TypeVar("PluginCollectionT", bound="PluginCollectionBase")


class PluginCollectionBase(ReadOnlyPluginCollectionBase, ABC):
    @property
    @abstractmethod
    def read_only_plugin_collection(self) -> ReadOnlyPluginCollectionBase:
        pass

    @abstractmethod
    def add_semantic_function(self, semantic_function: "KernelFunctionBase") -> "PluginCollectionBase":
        pass

    @abstractmethod
    def add_native_function(self, native_function: "KernelFunctionBase") -> "PluginCollectionBase":
        pass
