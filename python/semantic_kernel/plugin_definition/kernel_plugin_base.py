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

        name (str): The name of the plugin. The name can be upper/lower
            case letters and underscores.
        description (str): The description of the plugin.
    """

    name: Annotated[str, StringConstraints(pattern=r"^[A-Za-z_]+$", min_length=1)]
    description: Optional[str] = Field(default=None)

    @abstractmethod
    def __len__(self) -> int:
        """Define the len() operator for the plugin."""
        pass

    @abstractmethod
    def __contains__(self, function_name: str) -> bool:
        """Define the 'in' operator for the plugin."""
        pass

    @abstractmethod
    def get_function(self, function_name: str):
        """Gets the function in the plugin with the specified name."""
        pass

    @abstractmethod
    def __getitem__(self, name):
        """Define the [] operator for the plugin."""
        pass
