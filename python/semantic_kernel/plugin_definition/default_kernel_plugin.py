# Copyright (c) Microsoft. All rights reserved.

from typing import Dict

from pydantic import Field, model_validator

from semantic_kernel.orchestration.kernel_function_base import KernelFunctionBase
from semantic_kernel.plugin_definition.kernel_plugin import KernelPlugin


class DefaultKernelPlugin(KernelPlugin):
    """
    Represents a Kernel Plugin with functions.

    Attributes:
        name (str): The name of the plugin.
        description (str): The description of the plugin.
        functions (Dict[str, KernelFunctionBase]): The functions in the plugin,
            indexed by their name. Although this is a dictionary, the user
            should pass a list of KernelFunctionBase instances when initializing,
            and they will be automatically converted to a dictionary.
    """

    functions: Dict[str, "KernelFunctionBase"] = Field(default_factory=dict)

    @model_validator(mode="before")
    def list_to_dict(cls, values):
        """
        A model validator to construct the functions dictionary from the functions list.

        Args:
            values (Dict[str, Any]): The values to validate.

        Returns:
            The values, with the functions list converted to a dictionary.

        Raises:
            ValueError: If the functions list contains duplicate function names.
        """
        functions_list = values.get("functions", [])
        functions_dict = {}

        for function in functions_list:
            if function.name in functions_dict:
                raise ValueError(f"Duplicate function name detected: {function.name}")
            functions_dict[function.name] = function

        values["functions"] = functions_dict
        return values

    def get_function_count(self) -> int:
        """
        Gets the number of functions in the plugin.

        Returns:
            The number of functions in the plugin.

        """
        return len(self.functions)

    def has_function(self, function_name: str) -> bool:
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
    def from_function(cls, function: "KernelFunctionBase") -> "DefaultKernelPlugin":
        """
        Creates a DefaultKernelPlugin from a KernelFunctionBase instance.

        Args:
            function (KernelFunctionBase): The function to create the plugin from.

        Returns:
            A DefaultKernelPlugin instance.
        """
        return cls(name=function.name, description=function.description, functions=[function])
