# Copyright (c) Microsoft. All rights reserved.

import logging
from typing import TYPE_CHECKING, Any, ClassVar, Dict, Optional, Union

from pydantic import Field

from semantic_kernel.orchestration.sk_function import SKFunction
from semantic_kernel.plugin_definition import constants
from semantic_kernel.plugin_definition.functions_view import FunctionsView
from semantic_kernel.plugin_definition.plugin_collection_base import (
    PluginCollectionBase,
)
from semantic_kernel.plugin_definition.read_only_plugin_collection import (
    ReadOnlyPluginCollection,
)
from semantic_kernel.plugin_definition.read_only_plugin_collection_base import (
    ReadOnlyPluginCollectionBase,
)

if TYPE_CHECKING:
    from semantic_kernel.orchestration.sk_function_base import SKFunctionBase

logger: logging.Logger = logging.getLogger(__name__)


class PluginCollection(PluginCollectionBase):
    GLOBAL_PLUGIN: ClassVar[str] = constants.GLOBAL_PLUGIN
    read_only_plugin_collection_: ReadOnlyPluginCollection = Field(alias="read_only_plugin_collection")

    def __init__(
        self,
        log: Optional[Any] = None,
        plugin_collection: Union[Dict[str, Dict[str, SKFunction]], None] = None,
        read_only_plugin_collection_: Optional[ReadOnlyPluginCollection] = None,
    ) -> None:
        if log:
            logger.warning("The `log` parameter is deprecated. Please use the `logging` module instead.")
        if plugin_collection and read_only_plugin_collection_:
            raise ValueError("Only one of `plugin_collection` and `read_only_plugin_collection` can be" " provided")
        elif not plugin_collection and not read_only_plugin_collection_:
            read_only_plugin_collection = ReadOnlyPluginCollection({})
        elif not read_only_plugin_collection_:
            read_only_plugin_collection = ReadOnlyPluginCollection(plugin_collection)
        else:
            read_only_plugin_collection = read_only_plugin_collection_
        super().__init__(read_only_plugin_collection=read_only_plugin_collection)

    @property
    def read_only_plugin_collection(self) -> ReadOnlyPluginCollectionBase:
        return self.read_only_plugin_collection_

    @property
    def plugin_collection(self):
        return self.read_only_plugin_collection_.data

    def add_semantic_function(self, function: "SKFunctionBase") -> None:
        if function is None:
            raise ValueError("The function provided cannot be `None`")

        s_name, f_name = function.plugin_name, function.name
        s_name, f_name = s_name.lower(), f_name.lower()

        self.plugin_collection.setdefault(s_name, {})[f_name] = function

    def add_native_function(self, function: "SKFunctionBase") -> None:
        if function is None:
            raise ValueError("The function provided cannot be `None`")

        s_name, f_name = function.plugin_name, function.name
        s_name, f_name = self.read_only_plugin_collection_._normalize_names(s_name, f_name, True)

        self.plugin_collection.setdefault(s_name, {})[f_name] = function

    def has_function(self, plugin_name: Optional[str], function_name: str) -> bool:
        return self.read_only_plugin_collection_.has_function(plugin_name, function_name)

    def has_semantic_function(self, plugin_name: Optional[str], function_name: str) -> bool:
        return self.read_only_plugin_collection_.has_semantic_function(plugin_name, function_name)

    def has_native_function(self, plugin_name: Optional[str], function_name: str) -> bool:
        return self.read_only_plugin_collection_.has_native_function(plugin_name, function_name)

    def get_semantic_function(self, plugin_name: Optional[str], function_name: str) -> "SKFunctionBase":
        return self.read_only_plugin_collection_.get_semantic_function(plugin_name, function_name)

    def get_native_function(self, plugin_name: Optional[str], function_name: str) -> "SKFunctionBase":
        return self.read_only_plugin_collection_.get_native_function(plugin_name, function_name)

    def get_functions_view(self, include_semantic: bool = True, include_native: bool = True) -> FunctionsView:
        return self.read_only_plugin_collection_.get_functions_view(include_semantic, include_native)

    def get_function(self, plugin_name: Optional[str], function_name: str) -> "SKFunctionBase":
        return self.read_only_plugin_collection_.get_function(plugin_name, function_name)
