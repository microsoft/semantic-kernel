# Copyright (c) Microsoft. All rights reserved.

import importlib
import inspect
import logging
import os
from collections.abc import Generator, ItemsView
from functools import singledispatchmethod
from glob import glob
from types import MethodType
from typing import TYPE_CHECKING, Annotated, Any, TypeVar

from pydantic import Field, StringConstraints

from semantic_kernel.exceptions import PluginInitializationError
from semantic_kernel.exceptions.function_exceptions import FunctionInitializationError
from semantic_kernel.functions.kernel_function import KernelFunction
from semantic_kernel.functions.kernel_function_from_method import KernelFunctionFromMethod
from semantic_kernel.functions.kernel_function_from_prompt import KernelFunctionFromPrompt
from semantic_kernel.functions.types import KERNEL_FUNCTION_TYPE
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.kernel_types import OptionalOneOrMany
from semantic_kernel.utils.validation import PLUGIN_NAME_REGEX

if TYPE_CHECKING:
    from semantic_kernel.connectors.openapi_plugin.openapi_function_execution_parameters import (
        OpenAPIFunctionExecutionParameters,
    )
    from semantic_kernel.data.text_search import TextSearch
    from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata

logger = logging.getLogger(__name__)

_T = TypeVar("_T", bound="KernelPlugin")


class KernelPlugin(KernelBaseModel):
    """Represents a Kernel Plugin with functions.

    This class behaves mostly like a dictionary, with functions as values and their names as keys.
    When you add a function, through `.set` or `__setitem__`, the function is copied, the metadata is deep-copied
    and the name of the plugin is set in the metadata and added to the dict of functions.
    This is done in the same way as a normal dict, so a existing key will be overwritten.

    Attributes:
        name (str): The name of the plugin. The name can be upper/lower
            case letters and underscores.
        description (str): The description of the plugin.
        functions (Dict[str, KernelFunction]): The functions in the plugin,
            indexed by their name.

    Methods:
        set: Set a function in the plugin.
        __setitem__: Set a function in the plugin.
        get: Get a function from the plugin.
        __getitem__: Get a function from the plugin.
        __contains__: Check if a function is in the plugin.
        __iter__: Iterate over the functions in the plugin.
        update: Update the plugin with the functions from another.
        setdefault: Set a default value for a key.
        get_functions_metadata: Get the metadata for the functions in the plugin.

    Class methods:
        from_object(plugin_name: str, plugin_instance: Any | dict[str, Any], description: str | None = None):
            Create a plugin from a existing object, like a custom class with annotated functions.
        from_directory(plugin_name: str, parent_directory: str, description: str | None = None):
            Create a plugin from a directory, parsing:
            .py files, .yaml files and directories with skprompt.txt and config.json files.
        from_openapi(
                plugin_name: str,
                openapi_document_path: str,
                execution_settings: OpenAPIFunctionExecutionParameters | None = None,
                description: str | None = None):
            Create a plugin from an OpenAPI document.

    """

    name: Annotated[str, StringConstraints(pattern=PLUGIN_NAME_REGEX, min_length=1)]
    description: str | None = None
    functions: dict[str, KernelFunction] = Field(default_factory=dict)

    def __init__(
        self,
        name: str,
        description: str | None = None,
        functions: (OptionalOneOrMany[KERNEL_FUNCTION_TYPE | "KernelPlugin"] | dict[str, KERNEL_FUNCTION_TYPE]) = None,
    ):
        """Create a KernelPlugin.

        Args:
            name: The name of the plugin. The name can be upper/lower case letters and underscores.
            description: The description of the plugin.
            functions: The functions in the plugin, will be rewritten to a dictionary of functions.

        Raises:
            ValueError: If the functions are not of the correct type.
            PydanticError: If the name is not a valid plugin name.
        """
        super().__init__(
            name=name,
            description=description,
            functions=self._validate_functions(functions=functions, plugin_name=name),
        )

    # region Dict-like methods

    def __setitem__(self, key: str, value: KERNEL_FUNCTION_TYPE) -> None:
        """Sets a function in the plugin.

        This function uses plugin[function_name] = function syntax.

        Args:
            key (str): The name of the function.
            value (KernelFunction): The function to set.

        """
        self.functions[key] = KernelPlugin._parse_or_copy(value, self.name)

    def set(self, key: str, value: KERNEL_FUNCTION_TYPE) -> None:
        """Set a function in the plugin.

        This function uses plugin.set(function_name, function) syntax.

        Args:
            key (str): The name of the function.
            value (KernelFunction): The function to set.

        """
        self[key] = value

    def __getitem__(self, key: str) -> KernelFunction:
        """Get a function from the plugin.

        Using plugin[function_name] syntax.
        """
        return self.functions[key]

    def get(self, key: str, default: KernelFunction | None = None) -> KernelFunction | None:
        """Get a function from the plugin.

        Args:
            key (str): The name of the function.
            default (KernelFunction, optional): The default function to return if the key is not found.
        """
        return self.functions.get(key, default)

    def update(self, *args: Any, **kwargs: KernelFunction) -> None:
        """Update the plugin with the functions from another.

        Args:
            *args: The functions to update the plugin with, can be a dict, list or KernelPlugin.
            **kwargs: The kernel functions to update the plugin with.

        """
        if len(args) > 1:
            raise TypeError("update expected at most 1 arguments, got %d" % len(args))
        if args:
            if isinstance(args[0], KernelPlugin):
                self.add(args[0].functions)
            else:
                self.add(args[0])
        self.add(kwargs)

    @singledispatchmethod
    def add(self, functions: Any) -> None:
        """Add functions to the plugin."""
        raise TypeError(f"Unknown type being added, type was {type(functions)}")

    @add.register(list)
    def add_list(self, functions: list[KERNEL_FUNCTION_TYPE | "KernelPlugin"]) -> None:
        """Add a list of functions to the plugin."""
        for function in functions:
            if isinstance(function, KernelPlugin):
                self.add(function.functions)
                continue
            function = KernelPlugin._parse_or_copy(function, self.name)
            self[function.name] = function

    @add.register(dict)
    def add_dict(self, functions: dict[str, KERNEL_FUNCTION_TYPE]) -> None:
        """Add a dictionary of functions to the plugin."""
        for name, function in functions.items():
            self[name] = function

    def setdefault(self, key: str, value: KernelFunction | None = None):
        """Set a default value for a key."""
        if key not in self.functions:
            if value is None:
                raise ValueError("Value must be provided for new key.")
            self[key] = value
        return self[key]

    def __iter__(self) -> Generator[KernelFunction, None, None]:  # type: ignore
        """Iterate over the functions in the plugin."""
        yield from self.functions.values()

    def __contains__(self, key: str) -> bool:
        """Check if a function is in the plugin."""
        return key in self.functions

    # endregion
    # region Properties

    def get_functions_metadata(self) -> list["KernelFunctionMetadata"]:
        """Get the metadata for the functions in the plugin.

        Returns:
            A list of KernelFunctionMetadata instances.
        """
        return [func.metadata for func in self]

    # endregion
    # region Class Methods

    @classmethod
    def from_object(
        cls: type[_T],
        plugin_name: str,
        plugin_instance: Any | dict[str, Any],
        description: str | None = None,
    ) -> _T:
        """Creates a plugin that wraps the specified target object and imports it into the kernel's plugin collection.

        Args:
            plugin_name (str): The name of the plugin. Allows chars: upper, lower ASCII and underscores.
            plugin_instance (Any | dict[str, Any]): The plugin instance. This can be a custom class or a
                dictionary of classes that contains methods with the kernel_function decorator for one or
                several methods. See `TextMemoryPlugin` as an example.
            description (str | None): The description of the plugin.

        Returns:
            KernelPlugin: The imported plugin of type KernelPlugin.
        """
        functions: list[KernelFunction] = []
        candidates: list[tuple[str, MethodType]] | ItemsView[str, Any] = []

        if isinstance(plugin_instance, dict):
            candidates = plugin_instance.items()
        else:
            candidates = inspect.getmembers(plugin_instance, inspect.ismethod)
            candidates.extend(inspect.getmembers(plugin_instance, inspect.isfunction))  # type: ignore
            candidates.extend(inspect.getmembers(plugin_instance, inspect.iscoroutinefunction))  # type: ignore
        # Read every method from the plugin instance
        functions = [
            KernelFunctionFromMethod(method=candidate, plugin_name=plugin_name)
            for _, candidate in candidates
            if hasattr(candidate, "__kernel_function__")
        ]
        if not description:
            description = getattr(plugin_instance, "description", None)
        return cls(name=plugin_name, description=description, functions=functions)

    @classmethod
    def from_directory(
        cls: type[_T],
        plugin_name: str,
        parent_directory: str,
        description: str | None = None,
        class_init_arguments: dict[str, dict[str, Any]] | None = None,
    ) -> _T:
        """Create a plugin from a specified directory.

        This method does not recurse into subdirectories beyond one level deep from the specified plugin directory.
        For YAML files, function names are extracted from the content of the YAML files themselves (the name property).
        For directories, the function name is assumed to be the name of the directory. Each KernelFunction object is
        initialized with data parsed from the associated files and added to a list of functions that are then assigned
        to the created KernelPlugin object.
        A .py file is parsed and a plugin created,
        the functions within as then combined with any other functions found.
        The python file needs to contain a class with one or more kernel_function decorated methods.
        If this class has a `__init__` method, it will be called with the arguments provided in the
        `class_init_arguments` dictionary, the key needs to be the same as the name of the class,
        with the value being a dictionary of arguments to pass to the class (using kwargs).

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
            class_init_arguments (dict[str, dict[str, Any]] | None): The class initialization arguments

        Returns:
            KernelPlugin: The created plugin of type KernelPlugin.

        Raises:
            PluginInitializationError: If the plugin directory does not exist.
            PluginInvalidNameError: If the plugin name is invalid.
        """
        plugin_directory = os.path.abspath(os.path.join(parent_directory, plugin_name))
        if not os.path.exists(plugin_directory):
            raise PluginInitializationError(f"Plugin directory does not exist: {plugin_name}")

        functions: list[KernelFunction] = []
        for object in glob(os.path.join(plugin_directory, "*")):
            logger.debug(f"Found object: {object}")
            if os.path.isdir(object):
                if os.path.basename(object).startswith("__"):
                    continue
                try:
                    functions.append(KernelFunctionFromPrompt.from_directory(path=object))
                except FunctionInitializationError:
                    logger.warning(f"Failed to create function from directory: {object}")
            elif object.endswith(".yaml") or object.endswith(".yml"):
                with open(object) as file:
                    try:
                        functions.append(KernelFunctionFromPrompt.from_yaml(file.read()))
                    except FunctionInitializationError:
                        logger.warning(f"Failed to create function from YAML file: {object}")
            elif object.endswith(".py"):
                try:
                    functions.extend(
                        cls.from_python_file(
                            plugin_name=plugin_name,
                            py_file=object,
                            description=description,
                            class_init_arguments=class_init_arguments,
                        )
                    )
                except PluginInitializationError:
                    logger.warning(f"Failed to create function from Python file: {object}")
            else:
                logger.warning(f"Unknown file found: {object}")
        if not functions:
            raise PluginInitializationError(f"No functions found in folder: {parent_directory}/{plugin_name}")
        return cls(name=plugin_name, description=description, functions=functions)

    @classmethod
    def from_openapi(
        cls: type[_T],
        plugin_name: str,
        openapi_document_path: str | None = None,
        openapi_parsed_spec: dict[str, Any] | None = None,
        execution_settings: "OpenAPIFunctionExecutionParameters | None" = None,
        description: str | None = None,
    ) -> _T:
        """Create a plugin from an OpenAPI document.

        Args:
            plugin_name: The name of the plugin
            openapi_document_path: The path to the OpenAPI document (optional)
            openapi_parsed_spec: The parsed OpenAPI spec (optional)
            execution_settings: The execution parameters
            description: The description of the plugin

        Returns:
            KernelPlugin: The created plugin

        Raises:
            PluginInitializationError: if the plugin URL or plugin JSON/YAML is not provided
        """
        from semantic_kernel.connectors.openapi_plugin.openapi_manager import create_functions_from_openapi

        if not openapi_document_path and not openapi_parsed_spec:
            raise PluginInitializationError("Either the OpenAPI document path or a parsed OpenAPI spec is required.")

        return cls(  # type: ignore
            name=plugin_name,
            description=description,
            functions=create_functions_from_openapi(  # type: ignore
                plugin_name=plugin_name,
                openapi_document_path=openapi_document_path,
                openapi_parsed_spec=openapi_parsed_spec,
                execution_settings=execution_settings,
            ),
        )

    @classmethod
    def from_python_file(
        cls: type[_T],
        plugin_name: str,
        py_file: str,
        description: str | None = None,
        class_init_arguments: dict[str, dict[str, Any]] | None = None,
    ) -> _T:
        """Create a plugin from a Python file."""
        module_name = os.path.basename(py_file).replace(".py", "")
        spec = importlib.util.spec_from_file_location(module_name, py_file)
        if not spec:
            raise PluginInitializationError(f"Could not load spec from file {py_file}")
        module = importlib.util.module_from_spec(spec)
        if not module or not spec.loader:
            raise PluginInitializationError(f"No module found in file {py_file}")
        spec.loader.exec_module(module)

        for name, cls_instance in inspect.getmembers(module, inspect.isclass):
            if cls_instance.__module__ != module_name:
                continue
            # Check whether this class has at least one @kernel_function decorated method
            has_kernel_function = False
            for _, method in inspect.getmembers(cls_instance, inspect.isfunction):
                if getattr(method, "__kernel_function__", False):
                    has_kernel_function = True
                    break
            if not has_kernel_function:
                continue
            init_args = class_init_arguments.get(name, {}) if class_init_arguments else {}
            instance = getattr(module, name)(**init_args)
            return cls.from_object(plugin_name=plugin_name, description=description, plugin_instance=instance)
        raise PluginInitializationError(f"No class found in file: {py_file}")

    @classmethod
    def from_text_search_with_search(
        cls: type[_T],
        text_search: "TextSearch",
        plugin_name: str,
        plugin_description: str | None = None,
        **kwargs: Any,
    ) -> _T:
        """Creates a plugin that wraps the text search "search" function.

        Args:
            text_search: The text search to use.
            plugin_name: The name of the plugin.
            plugin_description: The description of the search plugin.
            **kwargs: The keyword arguments to use to create the search function.

        Returns:
            a KernelPlugin.
        """
        return cls(name=plugin_name, description=plugin_description, functions=[text_search.create_search(**kwargs)])

    @classmethod
    def from_text_search_with_get_text_search_results(
        cls: type[_T],
        text_search: "TextSearch",
        plugin_name: str,
        plugin_description: str | None = None,
        **kwargs: Any,
    ) -> _T:
        """Creates a plugin that wraps the text search "get_text_search_results" function.

        Args:
            text_search: The text search to use.
            plugin_name: The name of the plugin.
            plugin_description: The description of the search plugin.
            **kwargs: The keyword arguments to use to create the search function.

        Returns:
            a KernelPlugin.
        """
        return cls(
            name=plugin_name,
            description=plugin_description,
            functions=[text_search.create_get_text_search_results(**kwargs)],
        )

    @classmethod
    def from_text_search_with_get_search_results(
        cls: type[_T],
        text_search: "TextSearch",
        plugin_name: str,
        plugin_description: str | None = None,
        **kwargs: Any,
    ) -> _T:
        """Creates a plugin that wraps the text search "get_search_results" function.

        Args:
            text_search: The text search to use.
            plugin_name: The name of the plugin.
            plugin_description: The description of the search plugin.
            **kwargs: The keyword arguments to use to create the search function.

        Returns:
            a KernelPlugin.
        """
        return cls(
            name=plugin_name,
            description=plugin_description,
            functions=[text_search.create_get_search_results(**kwargs)],
        )

    # endregion
    # region Internal Static Methods

    @staticmethod
    def _validate_functions(
        functions: OptionalOneOrMany[KERNEL_FUNCTION_TYPE | "KernelPlugin"] | dict[str, KERNEL_FUNCTION_TYPE],
        plugin_name: str,
    ) -> dict[str, "KernelFunction"]:
        """Validates the functions and returns a dictionary of functions."""
        if not functions or not plugin_name:
            # if the plugin_name is not present, the validation will fail, so no point in parsing.
            return {}
        if isinstance(functions, dict):
            return {
                name: KernelPlugin._parse_or_copy(function=function, plugin_name=plugin_name)
                for name, function in functions.items()
            }
        if isinstance(functions, KernelPlugin):
            return {
                name: function.function_copy(plugin_name=plugin_name) for name, function in functions.functions.items()
            }
        if isinstance(functions, KernelFunction):
            return {functions.name: KernelPlugin._parse_or_copy(function=functions, plugin_name=plugin_name)}
        if callable(functions):
            function = KernelPlugin._parse_or_copy(function=functions, plugin_name=plugin_name)
            return {function.name: function}
        if isinstance(functions, list):
            functions_dict: dict[str, KernelFunction] = {}
            for function in functions:  # type: ignore
                if isinstance(function, KernelFunction) or callable(function):
                    function = KernelPlugin._parse_or_copy(function=function, plugin_name=plugin_name)
                    functions_dict[function.name] = function
                elif isinstance(function, KernelPlugin):  # type: ignore
                    functions_dict.update({
                        name: KernelPlugin._parse_or_copy(function=function, plugin_name=plugin_name)
                        for name, function in function.functions.items()
                    })
                else:
                    raise ValueError(f"Invalid type for functions in list: {function} (type: {type(function)})")
            return functions_dict
        raise ValueError(f"Invalid type for supplied functions: {functions} (type: {type(functions)})")

    @staticmethod
    def _parse_or_copy(function: KERNEL_FUNCTION_TYPE, plugin_name: str) -> "KernelFunction":
        """Handle the function and return a KernelFunction instance."""
        if isinstance(function, KernelFunction):
            return function.function_copy(plugin_name=plugin_name)
        if callable(function):
            return KernelFunctionFromMethod(method=function, plugin_name=plugin_name)
        raise ValueError(f"Invalid type for function: {function} (type: {type(function)})")

    # endregion
