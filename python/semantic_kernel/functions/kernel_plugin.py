# Copyright (c) Microsoft. All rights reserved.

import sys
from typing import TYPE_CHECKING, Dict, List, Optional, Union

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated

from pydantic import Field, StringConstraints

from semantic_kernel.exceptions import FunctionInvalidNameError
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.validation import PLUGIN_NAME_REGEX

if TYPE_CHECKING:
    from semantic_kernel.functions.kernel_function import KernelFunction
    from semantic_kernel.functions.kernel_function_metadata import KernelFunctionMetadata


class KernelPlugin(KernelBaseModel):
    """
    Represents a Kernel Plugin with functions.

    Attributes:
        name (str): The name of the plugin. The name can be upper/lower
            case letters and underscores.
        description (str): The description of the plugin.
        functions (Dict[str, KernelFunction]): The functions in the plugin,
            indexed by their name.
    """

    name: Annotated[str, StringConstraints(pattern=PLUGIN_NAME_REGEX, min_length=1)]
    description: Optional[str] = Field(default=None)
    functions: Optional[Dict[str, "KernelFunction"]] = Field(default_factory=dict)

    def __init__(
        self,
        name: str,
        description: Optional[str] = None,
        functions: Optional[Union[List["KernelFunction"], Dict[str, "KernelFunction"]]] = None,
    ):
        """
        Initialize a new instance of the KernelPlugin class

        Args:
            name (str): The name of the plugin.
            description (Optional[str]): The description of the plugin.
            functions (List[KernelFunction]): The functions in the plugin.

        Raises:
            ValueError: If the functions list contains duplicate function names.
        """
        functions_dict = {}
        if functions is not None:
            if isinstance(functions, list):
                for function in functions:
                    if function.name in functions_dict:
                        raise FunctionInvalidNameError(f"Duplicate function name detected: {function.name}")
                    functions_dict[function.name] = function
            else:
                functions_dict = functions
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

    def __getitem__(self, name: str) -> "KernelFunction":
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
        cls, functions: List["KernelFunction"], plugin_name: str, description: Optional[str] = None
    ) -> "KernelPlugin":
        """
        Creates a KernelPlugin from a KernelFunction instance.

        Args:
            functions (List[KernelFunction]): The functions to create the plugin from.
            plugin_name (Optional[str]): The name of the plugin. If not specified,
                the name of the function will be used.
            description (Optional[str]): The description of the plugin.

        Returns:
            A KernelPlugin instance.
        """
        return cls(name=plugin_name, description=description, functions=functions)

    def get_functions_metadata(self) -> List["KernelFunctionMetadata"]:
        """
        Get the metadata for the functions in the plugin.

        Returns:
            A list of KernelFunctionMetadata instances.
        """
        return [func.metadata for func in self.functions.values()]
