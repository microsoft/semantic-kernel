# Copyright (c) Microsoft. All rights reserved.

from typing import Any, Dict, Iterable, List, Optional, TypeVar, Union

from pydantic import Field

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.orchestration.kernel_function_base import KernelFunctionBase
from semantic_kernel.plugin_definition.functions_view import FunctionsView
from semantic_kernel.plugin_definition.kernel_plugin import KernelPlugin

# To support Python 3.8, need to use TypeVar since Iterable is not scriptable
KernelPluginType = TypeVar("KernelPluginType", bound=KernelPlugin)


class KernelPluginCollection(KernelBaseModel):
    """
    The Kernel Plugin Collection class. This class is used to store a collection of plugins.

    Attributes:
        plugins (Dict[str, KernelPlugin]): The plugins in the collection, indexed by their name.
    """

    plugins: Optional[Dict[str, KernelPlugin]] = Field(default_factory=dict)

    def __init__(self, plugins: Union[None, "KernelPluginCollection", Iterable[KernelPluginType]] = None):
        """
        Initialize a new instance of the KernelPluginCollection class

        Args:
            plugins (Union[None, KernelPluginCollection, Iterable[KernelPlugin]]): The plugins to add
                to the collection. If None, an empty collection is created. If a KernelPluginCollection,
                the plugins are copied from the other collection. If an iterable of KernelPlugin,
                the plugins are added to the collection.

        Raises:
            ValueError: If the plugins is not None, a KernelPluginCollection, or an iterable of KernelPlugin.
        """
        if plugins is None:
            plugins = {}
        elif isinstance(plugins, KernelPluginCollection):
            # Extract plugins from another KernelPluginCollection instance
            plugins = {plugin.name: plugin for plugin in plugins.plugins.values()}
        elif isinstance(plugins, Iterable):
            # Process an iterable of plugins
            plugins = self._process_plugins_iterable(plugins)
        else:
            raise ValueError("Invalid type for plugins")

        super().__init__(plugins=plugins)

    @staticmethod
    def _process_plugins_iterable(plugins_input: Iterable[KernelPlugin]) -> Dict[str, KernelPlugin]:
        plugins_dict = {}
        for plugin in plugins_input:
            if plugin is None:
                raise ValueError("Plugin and plugin.name must not be None")
            if plugin.name in plugins_dict:
                raise ValueError(f"Duplicate plugin name detected: {plugin.name}")
            plugins_dict[plugin.name] = plugin
        return plugins_dict

    def add(self, plugin: KernelPlugin) -> None:
        """
        Add a single plugin to the collection

        Args:
            plugin (KernelPlugin): The plugin to add to the collection.

        Raises:
            ValueError: If the plugin or plugin.name is None.
        """
        if plugin is None:
            raise ValueError("Plugin must not be None")
        if plugin.name in self.plugins:
            raise ValueError(f"Plugin with name {plugin.name} already exists")
        self.plugins[plugin.name] = plugin

    def add_plugin_from_functions(self, plugin_name: str, functions: List["KernelFunctionBase"]) -> None:
        """
        Add a function to a new plugin in the collection

        Args:
            plugin_name (str): The name of the plugin to create.
            functions (List[KernelFunctionBase]): The functions to add to the plugin.

        Raises:
            ValueError: If the function or plugin_name is None or invalid.
        """
        if not functions or not plugin_name:
            raise ValueError("Functions or plugin_name must not be None or empty")
        if plugin_name in self.plugins:
            raise ValueError(f"Plugin with name {plugin_name} already exists")

        plugin = KernelPlugin.from_functions(plugin_name=plugin_name, functions=functions)
        self.plugins[plugin_name] = plugin

    def add_functions_to_plugin(self, functions: List["KernelFunctionBase"], plugin_name: str) -> None:
        """
        Add functions to a plugin in the collection

        Args:
            functions (List[KernelFunctionBase]): The function to add to the plugin.
            plugin_name (str): The name of the plugin to add the function to.

        Raises:
            ValueError: If the functions or plugin_name is None or invalid.
            ValueError: if the function already exists in the plugin.
        """
        if not functions or not plugin_name:
            raise ValueError("Functions and plugin_name must not be None or empty")

        if plugin_name not in self.plugins:
            self.plugins.add(KernelPlugin(name=plugin_name, functions=functions))
            return

        plugin = self.plugins[plugin_name]
        for func in functions:
            if func.name in plugin.functions:
                raise ValueError(f"Function with name '{func.name}' already exists in plugin '{plugin_name}'")
            plugin.functions[func.name] = func

    def add_list_of_plugins(self, plugins: List[KernelPlugin]) -> None:
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

    def remove_by_name(self, plugin_name: str) -> bool:
        """
        Remove a plugin from the collection by name

        Args:
            plugin_name (str): The name of the plugin to remove from the collection.

        Returns:
            True if the plugin was removed, False otherwise.
        """
        if plugin_name is None:
            return False
        return self.plugins.pop(plugin_name, None) is not None

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

    def __contains__(self, plugin_name: str) -> bool:
        """
        Check if the collection contains a plugin

        Args:
            plugin_name (str): The name of the plugin to check for.

        Returns:
            True if the collection contains the plugin, False otherwise.
        """
        if not plugin_name:
            return False
        return self.plugins.get(plugin_name) is not None
