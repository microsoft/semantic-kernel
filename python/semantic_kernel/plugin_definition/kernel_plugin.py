# Copyright (c) Microsoft. All rights reserved.

import re
from abc import ABC, abstractmethod
from typing import Optional

from pydantic import Field, field_validator

from semantic_kernel.kernel_pydantic import KernelBaseModel


class KernelPlugin(KernelBaseModel, ABC):
    """
    The KernelPlugin Base Class. All plugins must inherit from this class.

    Attributes:

        name (str): The name of the plugin.
        description (str): The description of the plugin.
    """

    name: str
    description: Optional[str] = Field(default=None)

    @field_validator("name", mode="after")
    @classmethod
    def name_must_be_valid(cls, v: str) -> str:
        """Validates that the name contains only uppercase, lowercase letters, or underscores."""
        pattern = r"^[A-Za-z_]+$"
        if not re.match(pattern, v):
            raise ValueError("Name must contain only uppercase, lowercase letters, or underscores")
        return v

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
