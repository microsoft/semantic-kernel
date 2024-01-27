# Copyright (c) Microsoft. All rights reserved.

from typing import Dict, List, Optional

from pydantic import Field

from semantic_kernel.orchestration.kernel_function_base import KernelFunctionBase
from semantic_kernel.plugin_definition.kernel_plugin_base import KernelPluginBase


class DefaultKernelPlugin(KernelPluginBase):
    """
    Represents a Kernel Plugin with functions.

    Attributes:
        name (str): The name of the plugin. The name can be upper/lower
            case letters and underscores.
        description (str): The description of the plugin.
        functions (Dict[str, KernelFunctionBase]): The functions in the plugin,
            indexed by their name. Although this is a dictionary, the user
            should pass a list of KernelFunctionBase instances when initializing,
            and they will be automatically converted to a dictionary.
    """

    functions: Optional[Dict[str, "KernelFunctionBase"]] = Field(default_factory=dict)

    def __init__(
        self, name: str, description: Optional[str] = None, functions: Optional[List[KernelFunctionBase]] = None
    ):
        """
        Initialize a new instance of the DefaultKernelPlugin class

        Args:
            name (str): The name of the plugin.
            description (Optional[str]): The description of the plugin.
            functions (List[KernelFunctionBase]): The functions in the plugin.

        Raises:
            ValueError: If the functions list contains duplicate function names.
        """
        functions_dict = {}
        if functions is not None:
            for function in functions:
                if function.name in functions_dict:
                    raise ValueError(f"Duplicate function name detected: {function.name}")
                functions_dict[function.name] = function
        super().__init__(name=name, description=description, functions=functions_dict)

    def __len__(self) -> int:
        """
        Gets the number of functions in the plugin.

        Returns:
            The number of functions in the plugin.

        """
        return len(self.functions)

    def __contains__(self, function_name: str) -> bool:
        """
        Checks if the plugin contains a function with the specified name.

        Args:
            function_name (str): The name of the function.

        Returns:
            True if the plugin contains a function with the specified name, False otherwise.
        """
        return function_name in self.functions.keys()

    def get_function(self, function_name: str):
        """
        Gets the function in the plugin with the specified name.

        Args:
            function_name (str): The name of the function.

        Returns:
            The function.

        Raises:
            KeyError: If the plugin does not contain a function with the specified name.
        """
        try:
            return self.functions[function_name]
        except KeyError:
            raise KeyError(
                f"The plugin does not contain a function with the specified name. "
                f"Plugin name: {self.name}, function name: {function_name}"
            )

    def __getitem__(self, name):
        """Define the [] operator for the plugin

        Args:
            name (str): The name of the function to retrieve.

        Returns:
            The function if it exists, None otherwise.

        Raises:
            KeyError: If the function does not exist.
        """
        if name not in self.functions:
            raise KeyError(f"Function {name} not found.")
        return self.functions[name]

    @classmethod
    def from_functions(
        cls, functions: List["KernelFunctionBase"], plugin_name: str, description: Optional[str] = None
    ) -> "DefaultKernelPlugin":
        """
        Creates a DefaultKernelPlugin from a KernelFunctionBase instance.

        Args:
            functions (List[KernelFunctionBase]): The functions to create the plugin from.
            plugin_name (Optional[str]): The name of the plugin. If not specified,
                the name of the function will be used.
            description (Optional[str]): The description of the plugin.

        Returns:
            A DefaultKernelPlugin instance.
        """
        return cls(name=plugin_name, description=description, functions=functions)
