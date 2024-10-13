# Copyright (c) Microsoft. All rights reserved.

<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
from typing import Any
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
from typing import Any
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
from typing import Any
=======
>>>>>>> Stashed changes
=======
from typing import Any
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< HEAD
from typing import Any
=======
from typing import List, Optional
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head

from pydantic import Field

from semantic_kernel.const import DEFAULT_FULLY_QUALIFIED_NAME_SEPARATOR
from semantic_kernel.functions.kernel_parameter_metadata import KernelParameterMetadata
from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.utils.validation import FUNCTION_NAME_REGEX, PLUGIN_NAME_REGEX


class KernelFunctionMetadata(KernelBaseModel):
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
<<<<<<< HEAD
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
=======
=======
<<<<<<< HEAD
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    """The kernel function metadata."""

    name: str = Field(..., pattern=FUNCTION_NAME_REGEX)
    plugin_name: str | None = Field(None, pattern=PLUGIN_NAME_REGEX)
    description: str | None = Field(default=None)
    parameters: list[KernelParameterMetadata] = Field(default_factory=list)
    is_prompt: bool
    is_asynchronous: bool | None = Field(default=True)
    return_parameter: KernelParameterMetadata | None = None
    additional_properties: dict[str, Any] | None = Field(default=None)

    @property
    def fully_qualified_name(self) -> str:
        """Get the fully qualified name of the function.

        A fully qualified name is the name of the combination of the plugin name and
        the function name, separated by a hyphen, if the plugin name is present.
        Otherwise, it is just the function name.

        Returns:
            The fully qualified name of the function.
        """
        return self.custom_fully_qualified_name(DEFAULT_FULLY_QUALIFIED_NAME_SEPARATOR)

    def custom_fully_qualified_name(self, separator: str) -> str:
        """Get the fully qualified name of the function with a custom separator.

        Args:
            separator (str): The custom separator.

        Returns:
            The fully qualified name of the function with a custom separator.
        """
        return f"{self.plugin_name}{separator}{self.name}" if self.plugin_name else self.name

    def __eq__(self, other: object) -> bool:
        """Compare to another KernelFunctionMetadata instance.
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
<<<<<<< div
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> head
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
=======
>>>>>>> Stashed changes
=======
=======
=======
=======
>>>>>>> Stashed changes
    name: str = Field(pattern=FUNCTION_NAME_REGEX)
    plugin_name: str = Field(pattern=PLUGIN_NAME_REGEX)
    description: Optional[str] = Field(default=None)
    parameters: List[KernelParameterMetadata] = Field(default_factory=list)
    is_prompt: bool
    is_asynchronous: Optional[bool] = Field(default=True)
    return_parameter: Optional[KernelParameterMetadata] = None

    def __eq__(self, other: "KernelFunctionMetadata") -> bool:
        """
        Compare to another KernelFunctionMetadata instance.
>>>>>>> f40c1f2075e2443c31c57c34f5f66c2711a8db75
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head

        Args:
            other (KernelFunctionMetadata): The other KernelFunctionMetadata instance.

        Returns:
            True if the two instances are equal, False otherwise.
        """
        if not isinstance(other, KernelFunctionMetadata):
            return False

        return (
            self.name == other.name
            and self.plugin_name == other.plugin_name
            and self.description == other.description
            and self.parameters == other.parameters
            and self.is_prompt == other.is_prompt
            and self.is_asynchronous == other.is_asynchronous
            and self.return_parameter == other.return_parameter
        )
