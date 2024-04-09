# Copyright (c) Microsoft. All rights reserved.
from __future__ import annotations

import importlib
import inspect
import json
import logging
import os
import sys
from collections.abc import Callable
from glob import glob
from types import MethodType
from typing import TYPE_CHECKING, Any, ItemsView, List

import httpx

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated

import yaml
from pydantic import Field, StringConstraints, ValidationInfo, field_validator
from pydantic.dataclasses import dataclass

from semantic_kernel.connectors.openapi_plugin.openapi_manager import OpenAPIPlugin
from semantic_kernel.connectors.utils.document_loader import DocumentLoader
from semantic_kernel.exceptions import KernelPluginInvalidConfigurationError, PluginInitializationError
from semantic_kernel.functions.kernel_function import TEMPLATE_FORMAT_MAP, KernelFunction
from semantic_kernel.functions.kernel_function_from_method import KernelFunctionFromMethod
from semantic_kernel.functions.kernel_function_from_prompt import KernelFunctionFromPrompt
from semantic_kernel.prompt_template.prompt_template_config import PromptTemplateConfig
from semantic_kernel.utils.validation import PLUGIN_NAME_REGEX, validate_plugin_name

if TYPE_CHECKING:
    from semantic_kernel.connectors.openai_plugin.openai_authentication_config import OpenAIAuthenticationConfig
    from semantic_kernel.connectors.openai_plugin.openai_function_execution_parameters import (
        OpenAIFunctionExecutionParameters,
    )
    from semantic_kernel.connectors.openai_plugin.openai_utils import OpenAIUtils
    from semantic_kernel.connectors.openapi_plugin.openapi_function_execution_parameters import (
        OpenAPIFunctionExecutionParameters,
    )
    from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata

logger = logging.getLogger(__name__)


@dataclass
class KernelPlugin:
    """
    Represents a Kernel Plugin with functions.

    Attributes:
        name (str): The name of the plugin. The name can be upper/lower
            case letters and underscores.
        description (str): The description of the plugin.
        functions (Dict[str, KernelFunction]): The functions in the plugin,
            indexed by their name, this can be supplied as:
                - KernelFunction
                - Callable
                - list of KernelFunctions or Callables
                - dict of names and KernelFunctions or Callables
                - KernelPlugin
                - list of KernelPlugins
                - None

    Raises:
        ValueError: If the functions are not of the correct type.
        PydanticError: If the name is not a valid plugin name.
    """

    name: Annotated[str, StringConstraints(pattern=PLUGIN_NAME_REGEX, min_length=1)]
    description: str | None = None
    functions: dict[str, KernelFunction] = Field(default_factory=dict)

    # region Validators

    @field_validator("functions", mode="before")
    @classmethod
    def _validate_functions(
        cls,
        functions: (
            KernelFunction
            | Callable[..., Any]
            | list[KernelFunction | Callable[..., Any]]
            | dict[str, KernelFunction | Callable[..., Any]]
            | KernelPlugin
            | list[KernelPlugin]
            | None
        ),
        info: ValidationInfo,
    ) -> dict[str, KernelFunction]:
        """Validates the functions and returns a dictionary of functions."""
        plugin_name = info.data.get("name")
        if not functions or not plugin_name:
            # if the plugin_name is not present, the validation will fail, so no point in parsing.
            return {}
        if isinstance(functions, dict):
            return {
                name: cls._parse_or_copy(function=function, plugin_name=plugin_name)
                for name, function in functions.items()
            }
        if isinstance(functions, KernelPlugin):
            return {
                name: function.function_copy(plugin_name=plugin_name) for name, function in functions.functions.items()
            }
        if isinstance(functions, KernelFunction):
            return {functions.name: cls._parse_or_copy(function=functions, plugin_name=plugin_name)}
        if isinstance(functions, Callable):
            function = cls._parse_or_copy(function=functions, plugin_name=plugin_name)
            return {function.name: function}
        if isinstance(functions, list):
            functions_dict: dict[str, KernelFunction] = {}
            for function in functions:
                if isinstance(function, (KernelFunction, Callable)):
                    function = cls._parse_or_copy(function=function, plugin_name=plugin_name)
                    functions_dict[function.name] = function
                elif isinstance(function, KernelPlugin):  # type: ignore
                    functions_dict.update(
                        {
                            name: cls._parse_or_copy(function=function, plugin_name=plugin_name)
                            for name, function in function.functions.items()
                        }
                    )
                else:
                    raise ValueError(f"Invalid type for functions in list: {function} (type: {type(function)})")
            return functions_dict
        raise ValueError(f"Invalid type for supplied functions: {functions} (type: {type(functions)})")

    # endregion
    # region Dict like methods

    def __setitem__(self, key: str, value: KernelFunction) -> None:
        self.functions[key] = KernelPlugin._parse_or_copy(value, self.name)

    def set(self, key: str, value: KernelFunction) -> None:
        """Set a function in the plugin.

        Args:
            key (str): The name of the function.
            value (KernelFunction): The function to set.

        """
        self[key] = value

    def __getitem__(self, key: str) -> KernelFunction:
        return self.functions[key]

    def get(self, key: str, default: KernelFunction | None = None) -> KernelFunction | None:
        return self.functions.get(key, default)

    def update(self, *args: Any, **kwargs: Any) -> None:
        """Update the plugin with the functions from another.

        Args:
            *args: The functions to update the plugin with.

            **kwargs: The functions to update the plugin with.

        """
        if len(args) > 1:
            raise TypeError("update expected at most 1 arguments, got %d" % len(args))
        if args:
            other = args[0]
            if isinstance(other, KernelPlugin):
                other = other.functions
            if not isinstance(other, (dict, list)):
                raise TypeError(f"Expected dict, KernelPlugin or list as arg, got {type(other)}")
            if isinstance(other, dict):
                for key in other:
                    self[key] = other[key]
            else:
                for item in other:
                    if isinstance(item, KernelFunction):
                        self[item.name] = item
                    elif isinstance(item, KernelPlugin):
                        for key in item.functions:
                            self[key] = item.functions[key]
        if kwargs:
            for key in kwargs:
                if isinstance(kwargs[key], KernelFunction):
                    self[key] = kwargs[key]

    def setdefault(self, key: str, value: KernelFunction | None = None):
        if key not in self.functions:
            if value is None:
                raise ValueError("Value must be provided for new key.")
            self[key] = value
        return self[key]

    def __iter__(self):
        return iter(self.functions)

    def __contains__(self, key: str) -> bool:
        return key in self.functions

    # endregion
    # region Properties

    def get_functions_metadata(self) -> List["KernelFunctionMetadata"]:
        """
        Get the metadata for the functions in the plugin.

        Returns:
            A list of KernelFunctionMetadata instances.
        """
        return [func.metadata for func in self.functions.values()]

    # endregion
    # region Class Methods

    @classmethod
    def from_object(
        cls, plugin_name: str, plugin_instance: Any | dict[str, Any], description: str | None = None
    ) -> "KernelPlugin":
        """
        Creates a plugin that wraps the specified target object and imports it into the kernel's plugin collection

        Args:
            plugin_instance (Any | dict[str, Any]): The plugin instance. This can be a custom class or a
                dictionary of classes that contains methods with the kernel_function decorator for one or
                several methods. See `TextMemoryPlugin` as an example.
            plugin_name (str): The name of the plugin. Allows chars: upper, lower ASCII and underscores.

        Returns:
            KernelPlugin: The imported plugin of type KernelPlugin.
        """
        functions: list[KernelFunction] = []
        candidates: list[tuple[str, MethodType]] | ItemsView[str, Any] = []

        if isinstance(plugin_instance, dict):
            candidates = plugin_instance.items()
        else:
            candidates = inspect.getmembers(plugin_instance, inspect.ismethod)
        # Read every method from the plugin instance
        functions = [
            KernelFunctionFromMethod(method=candidate, plugin_name=plugin_name)
            for _, candidate in candidates
            if hasattr(candidate, "__kernel_function__")
        ]
        return cls(name=plugin_name, description=description, functions=functions)  # type: ignore

    @classmethod
    def from_directory(
        cls,
        plugin_name: str,
        parent_directory: str,
        description: str | None = None,
    ) -> "KernelPlugin":
        """Create a plugin from a specified directory.

        This method does not recurse into subdirectories beyond one level deep from the specified plugin directory.
        For YAML files, function names are extracted from the content of the YAML files themselves (the name property).
        For directories, the function name is assumed to be the name of the directory. Each KernelFunction object is
        initialized with data parsed from the associated files and added to a list of functions that are then assigned
        to the created KernelPlugin object.
        A native_function.py file is parsed and imported as a plugin,
        other functions found are then added to this plugin.

        Example:
            Assuming a plugin directory structure as follows:
        MyPlugins/
            |--- pluginA.yaml
            |--- pluginB.yaml
            |--- native_function.py
            |--- Directory1/
                |--- skprompt.txt
                |--- config.json
            |--- Directory2/
                |--- skprompt.txt
                |--- config.json

            Calling `KernelPlugin.from_directory("MyPlugins", "/path/to")` will create a KernelPlugin object named
                "MyPlugins", containing KernelFunction objects for `pluginA.yaml`, `pluginB.yaml`,
                `Directory1`, and `Directory2`, each initialized with their respective configurations.
                And functions for anything within native_function.py.

        Args:
            plugin_name (str): The name of the plugin, this is the name of the directory within the parent directory
            parent_directory (str): The parent directory path where the plugin directory resides
            description (str | None): The description of the plugin

        Returns:
            KernelPlugin: The created plugin of type KernelPlugin.

        Raises:
            PluginInitializationError: If the plugin directory does not exist.
            PluginInvalidNameError: If the plugin name is invalid.
        """
        MODULE_NAME = "native_function"

        plugin_directory = cls._validate_plugin_directory(
            parent_directory=parent_directory, plugin_directory_name=plugin_name
        )

        functions: list[KernelFunction] = []
        plugin = None

        # handle native python file at the root
        plugin_directory = os.path.abspath(os.path.join(parent_directory, plugin_name))
        native_py_file_path = os.path.join(plugin_directory, f"{MODULE_NAME}.py")
        if os.path.exists(native_py_file_path):
            spec = importlib.util.spec_from_file_location(MODULE_NAME, native_py_file_path)
            if not spec:
                raise PluginInitializationError(f"Failed to load plugin: {plugin_name}")
            module = importlib.util.module_from_spec(spec)
            assert spec.loader
            spec.loader.exec_module(module)

            class_name = next(
                (name for name, cls in inspect.getmembers(module, inspect.isclass) if cls.__module__ == MODULE_NAME),
                None,
            )
            if class_name:
                plugin_obj = getattr(module, class_name)()
                plugin = cls.from_object(plugin_name=plugin_name, plugin_instance=plugin_obj, description=description)

        # Handle YAML files at the root
        yaml_files = glob(os.path.join(plugin_directory, "*.yaml"))
        for yaml_file in yaml_files:
            with open(yaml_file, "r") as file:
                yaml_content = file.read()

                if not yaml_content:
                    raise PluginInitializationError("The input YAML string is empty")

                try:
                    data = yaml.safe_load(yaml_content)
                except yaml.YAMLError as exc:
                    raise PluginInitializationError(f"Error loading YAML: {exc}") from exc

                if not isinstance(data, dict):
                    raise PluginInitializationError("The YAML content must represent a dictionary")

                try:
                    prompt_template_config = PromptTemplateConfig(**data)
                except TypeError as exc:
                    raise PluginInitializationError(f"Error initializing PromptTemplateConfig: {exc}") from exc
                functions.append(
                    KernelFunctionFromPrompt(
                        function_name=prompt_template_config.name,
                        plugin_name=plugin_name,
                        description=prompt_template_config.description,
                        prompt_template_config=prompt_template_config,
                        template_format=prompt_template_config.template_format,
                    )
                )

        # Handle directories containing skprompt.txt and config.json
        for item in os.listdir(plugin_directory):
            item_path = os.path.join(plugin_directory, item)
            if os.path.isdir(item_path):
                prompt_path = os.path.join(item_path, "skprompt.txt")
                config_path = os.path.join(item_path, "config.json")

                if os.path.exists(prompt_path) and os.path.exists(config_path):
                    with open(config_path, "r") as config_file:
                        prompt_template_config = PromptTemplateConfig.from_json(config_file.read())
                    prompt_template_config.name = item

                    with open(prompt_path, "r") as prompt_file:
                        prompt = prompt_file.read()
                        prompt_template_config.template = prompt

                    prompt_template = TEMPLATE_FORMAT_MAP[prompt_template_config.template_format](  # type: ignore
                        prompt_template_config=prompt_template_config
                    )
                    functions.append(
                        KernelFunctionFromPrompt(
                            plugin_name=plugin_name,
                            prompt_template=prompt_template,
                            prompt_template_config=prompt_template_config,
                            template_format=prompt_template_config.template_format,
                            function_name=item,
                            description=prompt_template_config.description,
                        )
                    )
        if plugin:
            plugin.update(functions)
            return plugin
        if not functions:
            raise PluginInitializationError(f"No functions found in folder: {parent_directory}/{plugin_name}")
        return cls(name=plugin_name, description=description, functions=functions)

    @classmethod
    def from_openapi(
        cls,
        plugin_name: str,
        openapi_document_path: str,
        execution_settings: "OpenAIFunctionExecutionParameters | OpenAPIFunctionExecutionParameters | None" = None,
        description: str | None = None,
    ) -> "KernelPlugin":
        """Create a plugin from an OpenAPI document."""

        if not openapi_document_path:
            raise PluginInitializationError("OpenAPI document path is required.")

        return cls(
            name=plugin_name,
            description=description,
            functions=OpenAPIPlugin.create(
                plugin_name=plugin_name,
                openapi_document_path=openapi_document_path,
                execution_settings=execution_settings,
            ),
        )

    @classmethod
    async def from_openai(
        cls,
        plugin_name: str,
        plugin_url: str | None = None,
        plugin_str: str | None = None,
        execution_parameters: OpenAIFunctionExecutionParameters | None = None,
        description: str | None = None,
    ) -> "KernelPlugin":
        """Create a plugin from the Open AI manifest.

        Args:
            plugin_name (str): The name of the plugin
            plugin_url (str | None): The URL of the plugin
            plugin_str (str | None): The JSON string of the plugin
            execution_parameters (OpenAIFunctionExecutionParameters | None): The execution parameters

        Returns:
            KernelPlugin: The imported plugin

        Raises:
            PluginInitializationError: if the plugin URL or plugin JSON/YAML is not provided
        """

        if execution_parameters is None:
            execution_parameters = OpenAIFunctionExecutionParameters()

        if plugin_str is not None:
            # Load plugin from the provided JSON string/YAML string
            openai_manifest = plugin_str
        elif plugin_url is not None:
            # Load plugin from the URL
            http_client = execution_parameters.http_client if execution_parameters.http_client else httpx.AsyncClient()
            openai_manifest = await DocumentLoader.from_uri(
                url=plugin_url, http_client=http_client, auth_callback=None, user_agent=execution_parameters.user_agent
            )
        else:
            raise PluginInitializationError("Either plugin_url or plugin_json must be provided.")

        try:
            plugin_json = json.loads(openai_manifest)
            openai_auth_config = OpenAIAuthenticationConfig(**plugin_json["auth"])
        except json.JSONDecodeError as ex:
            raise KernelPluginInvalidConfigurationError("Parsing of Open AI manifest for auth config failed.") from ex

        # Modify the auth callback in execution parameters if it's provided
        if execution_parameters and execution_parameters.auth_callback:
            initial_auth_callback = execution_parameters.auth_callback

            async def custom_auth_callback(**kwargs: Any):
                return await initial_auth_callback(plugin_name, openai_auth_config, **kwargs)

            execution_parameters.auth_callback = custom_auth_callback

        try:
            openapi_spec_url = OpenAIUtils.parse_openai_manifest_for_openapi_spec_url(plugin_json=plugin_json)
        except PluginInitializationError as ex:
            raise KernelPluginInvalidConfigurationError(
                "Parsing of Open AI manifest for OpenAPI spec URL failed."
            ) from ex
        return cls(
            name=plugin_name,
            description=description,
            functions=OpenAPIPlugin.create(
                plugin_name=plugin_name,
                openapi_document_path=openapi_spec_url,
                execution_settings=execution_parameters,
            ),
        )

    # endregion
    # region Static Methods

    @staticmethod
    def _parse_or_copy(function: KernelFunction | Callable[..., Any], plugin_name: str) -> KernelFunction:
        """Handle the function and return a KernelFunction instance."""
        if isinstance(function, KernelFunction):
            return function.function_copy(plugin_name=plugin_name)
        if isinstance(function, Callable):
            return KernelFunctionFromMethod(method=function, plugin_name=plugin_name)
        raise ValueError(f"Invalid type for function: {function} (type: {type(function)})")

    @staticmethod
    def _validate_plugin_directory(parent_directory: str, plugin_directory_name: str) -> str:
        """Validate the plugin name and that the plugin directory exists.

        Args:
            parent_directory (str): The parent directory
            plugin_directory_name (str): The plugin directory name

        Returns:
            str: The plugin directory.

        Raises:
            PluginInitializationError: If the plugin directory does not exist.
            PluginInvalidNameError: If the plugin name is invalid.
        """
        validate_plugin_name(plugin_directory_name)

        plugin_directory = os.path.join(parent_directory, plugin_directory_name)
        plugin_directory = os.path.abspath(plugin_directory)

        if not os.path.exists(plugin_directory):
            raise PluginInitializationError(f"Plugin directory does not exist: {plugin_directory_name}")

        return plugin_directory

    # endregion
