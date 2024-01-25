# Copyright (c) Microsoft. All rights reserved.

from typing import Any, Dict, List, Optional

from pydantic import Field, model_validator

from semantic_kernel.functions.kernel_function_base import KernelFunctionBase
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.plugin_definition.default_kernel_plugin import DefaultKernelPlugin
from semantic_kernel.plugin_definition.functions_view import FunctionsView
from semantic_kernel.plugin_definition.kernel_plugin import KernelPlugin


class KernelPluginCollection(KernelBaseModel):
    """
    The Kernel Plugin Collection class. This class is used to store a collection of plugins.

    Attributes:
        plugins (Dict[str, KernelPlugin]): The plugins in the collection, indexed by their name.
    """
    plugins: Optional[Dict[str, KernelPlugin]] = Field(default_factory=dict)

    @model_validator(mode="before")
    def process_plugins(cls, values):
        """
        Processes the plugins input to the collection. This method is used to convert
        the plugins input to a dictionary of plugins, indexed by their name.

        Args:
            values (Dict[str, Any]): The values to validate.

        Returns:
            The values, with the plugins input converted to a dictionary.

        Raises:
            ValueError: If the plugins input is invalid.
        """
        plugins_input = values.get("plugins")
        if isinstance(plugins_input, KernelPluginCollection):
            # Extract plugins from another KernelPluginCollection instance
            values["plugins"] = {plugin.name: plugin for plugin in plugins_input.plugins.values()}
        elif isinstance(plugins_input, (list, set, tuple)):
            # Process an iterable of plugins
            plugins_dict = {}
            for plugin in plugins_input:
                if plugin is None or plugin.name is None:
                    raise ValueError("Plugin and plugin.name must not be None")
                if plugin.name in plugins_dict:
                    raise ValueError(f"Duplicate plugin name detected: {plugin.name}")
                plugins_dict[plugin.name] = plugin
            values["plugins"] = plugins_dict
        return values

    def add(self, plugin: KernelPlugin) -> None:
        """
        Add a single plugin to the collection

        Args:
            plugin (KernelPlugin): The plugin to add to the collection.

        Raises:
            ValueError: If the plugin or plugin.name is None.
        """
        if plugin is None or plugin.name is None:
            raise ValueError("Plugin and plugin.name must not be None")
        if plugin.name in self.plugins:
            raise ValueError(f"Plugin with name {plugin.name} already exists")
        self.plugins[plugin.name] = plugin

    def add_plugin_from_function(self, plugin_name: str, function: KernelFunctionBase) -> None:
        """
        Add a function to a new plugin in the collection

        Args:
            plugin_name (str): The name of the plugin to create.
            function (KernelFunctionBase): The function to add to the plugin.

        Raises:
            ValueError: If the function or plugin_name is None or invalid.
        """
        if not function or not plugin_name:
            raise ValueError("Function and plugin_name must not be None or empty")
        if plugin_name in self.plugins:
            raise ValueError(f"Plugin with name {plugin_name} already exists")

        plugin = DefaultKernelPlugin.from_function(function)
        self.plugins[plugin_name] = plugin

    def add_functions_to_plugin(self, functions: List[KernelFunctionBase], plugin_name: str) -> None:
        """
        Add a function to a plugin in the collection

        Args:
            functions (List[KernelFunctionBase]): The function to add to the plugin.
            plugin_name (str): The name of the plugin to add the function to.

        Raises:
            ValueError: If the function or plugin_name is None or invalid.
            ValueError: if the function already exists in the plugin.
        """
        if not functions or not plugin_name:
            raise ValueError("Functions and plugin_name must not be None or empty")
        if plugin_name not in self.plugins:
            raise ValueError(f"Plugin with name {plugin_name} does not exist")

        plugin = self.plugins[plugin_name]
        for func in functions:
            if func.name not in plugin.functions:
                plugin.functions[func.name] = func
            else:
                raise ValueError(f"Function with name '{func.name}' already exists in plugin '{plugin_name}'")

    def add_range(self, plugins: List[KernelPlugin]) -> None:
        """
        Add a list of plugins to the collection

        Args:
            plugins (List[KernelPlugin]): The plugins to add to the collection.

        Raises:
            ValueError: If the plugins list is None.
        """

        if plugins is None:
            raise ValueError("Plugins must not be None")
        for plugin in plugins:
            self.add(plugin)

    def remove(self, plugin: KernelPlugin) -> bool:
        """
        Remove a plugin from the collection

        Args:
            plugin (KernelPlugin): The plugin to remove from the collection.

        Returns:
            True if the plugin was removed, False otherwise.
        """
        if plugin is None or plugin.name is None:
            return False
        return self.plugins.pop(plugin.name, None) is not None

    def get_plugin(self, name: str) -> Optional[KernelPlugin]:
        """
        Get a plugin from the collection

        Args:
            name (str): The name of the plugin to retrieve.

        Returns:
            The plugin if it exists, None otherwise.
        """
        return self.plugins.get(name, None)

    def clear(self):
        """Clear the collection of all plugins"""
        self.plugins.clear()

    def get_functions_view(self, include_semantic: bool = True, include_native: bool = True) -> FunctionsView:
        """
        Get a view of the functions in the collection

        Args:
            include_semantic (bool): Whether to include semantic functions in the view.
            include_native (bool): Whether to include native functions in the view.

        Returns:
            A view of the functions in the collection.
        """
        result = FunctionsView()

        for _, plugin in self.plugins.items():
            for _, function in plugin.functions.items():
                if include_semantic and function.is_semantic:
                    result.add_function(function.describe())
                elif include_native and function.is_native:
                    result.add_function(function.describe())

        return result

    def __iter__(self) -> Any:
        """Define an iterator for the collection"""
        return iter(self.plugins.values())

    def __len__(self) -> int:
        """Define the length of the collection"""
        return len(self.plugins)

    def contains(self, plugin_name: str) -> bool:
        """Check if the collection contains a plugin"""
        if not plugin_name:
            return False
        return self.plugins.get(plugin_name) is not None

    def __getitem__(self, name):
        """Define the [] operator for the collection

        Args:
            name (str): The name of the plugin to retrieve.

        Returns:
            The plugin if it exists, None otherwise.

        Raises:
            KeyError: If the plugin does not exist.
        """
        if name not in self.plugins:
            raise KeyError(f"Plugin {name} not found.")
        return self.plugins[name]
