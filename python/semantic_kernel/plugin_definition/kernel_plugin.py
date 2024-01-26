# Copyright (c) Microsoft. All rights reserved.

import sys
from abc import ABC, abstractmethod
from typing import Optional

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated

from pydantic import Field, StringConstraints

from semantic_kernel.kernel_pydantic import KernelBaseModel


class KernelPluginBase(KernelBaseModel, ABC):
    """
    The KernelPluginBase Base Class. All plugins must inherit from this class.

    Attributes:

        name (str): The name of the plugin.
        description (str): The description of the plugin.
    """

    name: Annotated[str, StringConstraints(pattern=r"^[A-Za-z_]+$", min_length=1)]
    description: Optional[str] = Field(default=None)

    @abstractmethod
    def get_function_count(self) -> int:
        """Gets the number of functions in the plugin."""
        pass

    @abstractmethod
    def has_function(self, function_name: str) -> bool:
        """Checks if the plugin contains a function with the specified name."""
        pass

    @abstractmethod
    def get_function(self, function_name: str):
        """Gets the function in the plugin with the specified name."""
        pass

    @abstractmethod
    def __getitem__(self, name):
        """Define the [] operator for the plugin."""
        pass
