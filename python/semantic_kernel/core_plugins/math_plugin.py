# Copyright (c) Microsoft. All rights reserved.

from typing import Annotated

from semantic_kernel.functions.kernel_function_decorator import kernel_function


class MathPlugin:
    """Description: MathPlugin provides a set of functions to make Math calculations.

    Usage:
        kernel.add_plugin(MathPlugin(), plugin_name="math")

    Examples:
        {{math.Add}} => Returns the sum of input and amount (provided in the KernelArguments)
        {{math.Subtract}} => Returns the difference of input and amount (provided in the KernelArguments)
    """

    def _parse_number(self, val: int | float | str) -> float:
        """Helper to parse a value as a float (supports int, float, str)."""
        if isinstance(val, (int, float)):
            return float(val)
        try:
            return float(val)
        except Exception as ex:
            raise ValueError(f"Cannot convert {val!r} to float for math operation") from ex

    @kernel_function(name="Add")
    def add(
        self,
        input: Annotated[int | float | str, "The first number to add"],
        amount: Annotated[int | float | str, "The second number to add"],
    ) -> Annotated[float, "The result"]:
        """Returns the addition result of the values provided (supports float and int)."""
        x = self._parse_number(input)
        y = self._parse_number(amount)
        return x + y

    @kernel_function(name="Subtract")
    def subtract(
        self,
        input: Annotated[int | float | str, "The number to subtract from"],
        amount: Annotated[int | float | str, "The number to subtract"],
    ) -> Annotated[float, "The result"]:
        """Returns the difference of numbers provided (supports float and int)."""
        x = self._parse_number(input)
        y = self._parse_number(amount)
        return x - y
