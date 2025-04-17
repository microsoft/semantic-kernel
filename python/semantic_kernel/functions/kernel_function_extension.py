# Copyright (c) Microsoft. All rights reserved.

import logging
from abc import ABC
from collections.abc import Mapping, Sequence
from functools import singledispatchmethod
from typing import TYPE_CHECKING, Any, Literal, Protocol, runtime_checkable

from pydantic import Field, field_validator

from semantic_kernel.connectors.ai.prompt_execution_settings import PromptExecutionSettings
from semantic_kernel.exceptions import KernelFunctionNotFoundError, KernelPluginNotFoundError
from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata
from semantic_kernel.functions.kernel_plugin import KernelPlugin
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.prompt_template.const import KERNEL_TEMPLATE_FORMAT_NAME, TEMPLATE_FORMAT_TYPES
from semantic_kernel.prompt_template.prompt_template_base import PromptTemplateBase
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig

if TYPE_CHECKING:
    from semantic_kernel.connectors.openapi_plugin.openapi_function_execution_parameters import (
        OpenAPIFunctionExecutionParameters,
    )
    from semantic_kernel.functions.kernel_function import KernelFunction
    from semantic_kernel.functions.types import KERNEL_FUNCTION_TYPE
    from semantic_kernel.kernel import Kernel


logger: logging.Logger = logging.getLogger(__name__)


@runtime_checkable
class AddToKernelCallbackProtocol(Protocol):
    """Protocol for the callback to be called when the plugin is added to the kernel."""

    def added_to_kernel(self, kernel: "Kernel") -> None:
        """Called when the plugin is added to the kernel.

        Args:
            kernel (Kernel): The kernel instance
        """
        pass


class KernelFunctionExtension(KernelBaseModel, ABC):
    """Kernel function extension."""

    plugins: dict[str, KernelPlugin] = Field(default_factory=dict)

    @field_validator("plugins", mode="before")
    @classmethod
    def rewrite_plugins(
        cls, plugins: KernelPlugin | list[KernelPlugin] | dict[str, KernelPlugin] | None = None
    ) -> dict[str, KernelPlugin]:
        """Rewrite plugins to a dictionary."""
        if not plugins:
            return {}
        if isinstance(plugins, KernelPlugin):
            return {plugins.name: plugins}
        if isinstance(plugins, list):
            return {p.name: p for p in plugins}
        return plugins

    def add_plugin(
        self,
        plugin: KernelPlugin | object | dict[str, Any] | None = None,
        plugin_name: str | None = None,
        parent_directory: str | None = None,
        description: str | None = None,
        class_init_arguments: dict[str, dict[str, Any]] | None = None,
    ) -> "KernelPlugin":
        """Adds a plugin to the kernel's collection of plugins.

        If a plugin is provided, it uses that instance instead of creating a new KernelPlugin.
        See KernelPlugin.from_directory for more details on how the directory is parsed.

        Args:
            plugin: The plugin to add.
                This can be a KernelPlugin, in which case it is added straightaway and other parameters are ignored,
                a custom class that contains methods with the kernel_function decorator
                or a dictionary of functions with the kernel_function decorator for one or
                several methods.
                if the custom class has a `added_to_kernel` method, it will be called with the kernel instance.
            plugin_name: The name of the plugin, used if the plugin is not a KernelPlugin,
                if the plugin is None and the parent_directory is set,
                KernelPlugin.from_directory is called with those parameters,
                see `KernelPlugin.from_directory` for details.
            parent_directory: The parent directory path where the plugin directory resides
            description: The description of the plugin, used if the plugin is not a KernelPlugin.
            class_init_arguments: The class initialization arguments

        Returns:
            KernelPlugin: The plugin that was added.

        Raises:
            ValidationError: If a KernelPlugin needs to be created, but it is not valid.

        """
        if isinstance(plugin, KernelPlugin):
            self.plugins[plugin.name] = plugin
            return self.plugins[plugin.name]
        if not plugin_name:
            plugin_name = getattr(plugin, "name", plugin.__class__.__name__)
        if not isinstance(plugin_name, str):
            raise TypeError("plugin_name must be a string.")
        if plugin:
            self.plugins[plugin_name] = KernelPlugin.from_object(
                plugin_name=plugin_name, plugin_instance=plugin, description=description
            )
            if isinstance(plugin, AddToKernelCallbackProtocol):
                plugin.added_to_kernel(self)  # type: ignore
            return self.plugins[plugin_name]
        if plugin is None and parent_directory is not None:
            self.plugins[plugin_name] = KernelPlugin.from_directory(
                plugin_name=plugin_name,
                parent_directory=parent_directory,
                description=description,
                class_init_arguments=class_init_arguments,
            )
            return self.plugins[plugin_name]
        raise ValueError("plugin or parent_directory must be provided.")

    def add_plugins(self, plugins: list[KernelPlugin | object] | dict[str, KernelPlugin | object]) -> None:
        """Adds a list of plugins to the kernel's collection of plugins.

        Args:
            plugins (list[KernelPlugin] | dict[str, KernelPlugin]): The plugins to add to the kernel
        """
        if isinstance(plugins, list):
            for plug in plugins:
                self.add_plugin(plug)
            return
        for name, plugin in plugins.items():
            self.add_plugin(plugin, plugin_name=name)

    def add_function(
        self,
        plugin_name: str,
        function: "KERNEL_FUNCTION_TYPE | None" = None,
        function_name: str | None = None,
        description: str | None = None,
        prompt: str | None = None,
        prompt_template_config: PromptTemplateConfig | None = None,
        prompt_execution_settings: (
            PromptExecutionSettings | Sequence[PromptExecutionSettings] | Mapping[str, PromptExecutionSettings] | None
        ) = None,
        template_format: TEMPLATE_FORMAT_TYPES = KERNEL_TEMPLATE_FORMAT_NAME,
        prompt_template: PromptTemplateBase | None = None,
        return_plugin: bool = False,
        **kwargs: Any,
    ) -> "KernelFunction | KernelPlugin":
        """Adds a function to the specified plugin.

        Args:
            plugin_name (str): The name of the plugin to add the function to
            function (KernelFunction | Callable[..., Any]): The function to add
            function_name (str): The name of the function
            plugin_name (str): The name of the plugin
            description (str | None): The description of the function
            prompt (str | None): The prompt template.
            prompt_template_config (PromptTemplateConfig | None): The prompt template configuration
            prompt_execution_settings: The execution settings, will be parsed into a dict.
            template_format (str | None): The format of the prompt template
            prompt_template (PromptTemplateBase | None): The prompt template
            return_plugin (bool): If True, the plugin is returned instead of the function
            kwargs (Any): Additional arguments

        Returns:
            KernelFunction | KernelPlugin: The function that was added, or the plugin if return_plugin is True

        """
        from semantic_kernel.functions.kernel_function import KernelFunction

        if function is None:
            if not function_name or (not prompt and not prompt_template_config and not prompt_template):
                raise ValueError(
                    "function_name and prompt, prompt_template_config or prompt_template must be provided if a function is not supplied."  # noqa: E501
                )
            if prompt_execution_settings is None and (
                prompt_template_config is None or prompt_template_config.execution_settings is None
            ):
                prompt_execution_settings = PromptExecutionSettings(extension_data=kwargs)

            function = KernelFunction.from_prompt(
                function_name=function_name,
                plugin_name=plugin_name,
                description=description or (prompt_template_config.description if prompt_template_config else None),
                prompt=prompt,
                template_format=template_format,
                prompt_template=prompt_template,
                prompt_template_config=prompt_template_config,
                prompt_execution_settings=prompt_execution_settings,
            )
        elif not isinstance(function, KernelFunction):
            function = KernelFunction.from_method(plugin_name=plugin_name, method=function)
        if plugin_name not in self.plugins:
            plugin = KernelPlugin(name=plugin_name, functions=function)
            self.add_plugin(plugin)
            return plugin if return_plugin else plugin[function.name]
        self.plugins[plugin_name][function.name] = function
        return self.plugins[plugin_name] if return_plugin else self.plugins[plugin_name][function.name]

    def add_functions(
        self,
        plugin_name: str,
        functions: "list[KERNEL_FUNCTION_TYPE] | dict[str, KERNEL_FUNCTION_TYPE]",
    ) -> "KernelPlugin":
        """Adds a list of functions to the specified plugin.

        Args:
            plugin_name (str): The name of the plugin to add the functions to
            functions (list[KernelFunction] | dict[str, KernelFunction]): The functions to add

        Returns:
            KernelPlugin: The plugin that the functions were added to.

        """
        if plugin_name in self.plugins:
            self.plugins[plugin_name].update(functions)
            return self.plugins[plugin_name]
        return self.add_plugin(KernelPlugin(name=plugin_name, functions=functions))  # type: ignore

    def add_plugin_from_openapi(
        self,
        plugin_name: str,
        openapi_document_path: str | None = None,
        openapi_parsed_spec: dict[str, Any] | None = None,
        execution_settings: "OpenAPIFunctionExecutionParameters | None" = None,
        description: str | None = None,
    ) -> KernelPlugin:
        """Add a plugin from the OpenAPI manifest.

        Args:
            plugin_name: The name of the plugin
            openapi_document_path: The path to the OpenAPI document
            openapi_parsed_spec: The parsed OpenAPI spec
            execution_settings: The execution parameters
            description: The description of the plugin

        Returns:
            KernelPlugin: The imported plugin

        Raises:
            PluginInitializationError: if the plugin URL or plugin JSON/YAML is not provided
        """
        return self.add_plugin(
            KernelPlugin.from_openapi(
                plugin_name=plugin_name,
                openapi_document_path=openapi_document_path,
                openapi_parsed_spec=openapi_parsed_spec,
                execution_settings=execution_settings,
                description=description,
            )
        )

    def get_plugin(self, plugin_name: str) -> "KernelPlugin":
        """Get a plugin by name.

        Args:
            plugin_name (str): The name of the plugin

        Returns:
            KernelPlugin: The plugin

        Raises:
            KernelPluginNotFoundError: If the plugin is not found

        """
        if plugin_name not in self.plugins:
            raise KernelPluginNotFoundError(f"Plugin '{plugin_name}' not found")
        return self.plugins[plugin_name]

    def get_function(self, plugin_name: str | None, function_name: str) -> "KernelFunction":
        """Get a function by plugin_name and function_name.

        Args:
            plugin_name (str | None): The name of the plugin
            function_name (str): The name of the function

        Returns:
            KernelFunction: The function

        Raises:
            KernelPluginNotFoundError: If the plugin is not found
            KernelFunctionNotFoundError: If the function is not found

        """
        if plugin_name is None:
            for plugin in self.plugins.values():
                if function_name in plugin:
                    return plugin[function_name]
            raise KernelFunctionNotFoundError(f"Function '{function_name}' not found in any plugin.")
        if plugin_name not in self.plugins:
            raise KernelPluginNotFoundError(f"Plugin '{plugin_name}' not found")
        if function_name not in self.plugins[plugin_name]:
            raise KernelFunctionNotFoundError(f"Function '{function_name}' not found in plugin '{plugin_name}'")
        return self.plugins[plugin_name][function_name]

    def get_function_from_fully_qualified_function_name(self, fully_qualified_function_name: str) -> "KernelFunction":
        """Get a function by its fully qualified name (<plugin_name>-<function_name>).

        Args:
            fully_qualified_function_name (str): The fully qualified name of the function,
                if there is no '-' in the name, it is assumed that it is only a function_name.

        Returns:
            KernelFunction: The function

        Raises:
            KernelPluginNotFoundError: If the plugin is not found
            KernelFunctionNotFoundError: If the function is not found

        """
        names = fully_qualified_function_name.split("-", maxsplit=1)
        if len(names) == 1:
            plugin_name = None
            function_name = names[0]
        else:
            plugin_name = names[0]
            function_name = names[1]
        return self.get_function(plugin_name, function_name)

    def get_full_list_of_function_metadata(self) -> list["KernelFunctionMetadata"]:
        """Get a list of all function metadata in the plugins."""
        if not self.plugins:
            return []
        return [func.metadata for plugin in self.plugins.values() for func in plugin]

    @singledispatchmethod
    def get_list_of_function_metadata(self, *args: Any, **kwargs: Any) -> list["KernelFunctionMetadata"]:
        """Get a list of all function metadata in the plugin collection."""
        raise NotImplementedError("This method is not implemented for the provided arguments.")

    @get_list_of_function_metadata.register(bool)
    def get_list_of_function_metadata_bool(
        self, include_prompt: bool = True, include_native: bool = True
    ) -> list["KernelFunctionMetadata"]:
        """Get a list of the function metadata in the plugin collection.

        Args:
            include_prompt (bool): Whether to include semantic functions in the list.
            include_native (bool): Whether to include native functions in the list.

        Returns:
            A list of KernelFunctionMetadata objects in the collection.
        """
        if not self.plugins:
            return []
        return [
            func.metadata
            for plugin in self.plugins.values()
            for func in plugin.functions.values()
            if (include_prompt and func.is_prompt) or (include_native and not func.is_prompt)
        ]

    @get_list_of_function_metadata.register(dict)
    def get_list_of_function_metadata_filters(
        self,
        filters: dict[
            Literal["excluded_plugins", "included_plugins", "excluded_functions", "included_functions"], list[str]
        ],
    ) -> list["KernelFunctionMetadata"]:
        """Get a list of Kernel Function Metadata based on filters.

        Args:
            filters (dict[str, list[str]]): The filters to apply to the function list.
                The keys are:
                    - included_plugins: A list of plugin names to include.
                    - excluded_plugins: A list of plugin names to exclude.
                    - included_functions: A list of function names to include.
                    - excluded_functions: A list of function names to exclude.
                The included and excluded parameters are mutually exclusive.
                The function names are checked against the fully qualified name of a function.

        Returns:
            list[KernelFunctionMetadata]: The list of Kernel Function Metadata that match the filters.
        """
        if not self.plugins:
            return []
        included_plugins = filters.get("included_plugins")
        excluded_plugins = filters.get("excluded_plugins", [])
        included_functions = filters.get("included_functions")
        excluded_functions = filters.get("excluded_functions", [])
        if included_plugins and excluded_plugins:
            raise ValueError("Cannot use both included_plugins and excluded_plugins at the same time.")
        if included_functions and excluded_functions:
            raise ValueError("Cannot use both included_functions and excluded_functions at the same time.")

        result: list["KernelFunctionMetadata"] = []
        for plugin_name, plugin in self.plugins.items():
            if plugin_name in excluded_plugins or (included_plugins and plugin_name not in included_plugins):
                continue
            for function in plugin:
                if function.fully_qualified_name in excluded_functions or (
                    included_functions and function.fully_qualified_name not in included_functions
                ):
                    continue
                result.append(function.metadata)
        return result
