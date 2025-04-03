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

    @kernel_function(name="Add")
    def add(
        self,
        input: Annotated[int | str, "The first number to add"],
        amount: Annotated[int | str, "The second number to add"],
    ) -> Annotated[int, "The result"]:
        """Returns the Addition result of the values provided."""
        if isinstance(input, str):
            input = int(input)
        if isinstance(amount, str):
            amount = int(amount)

        return input + amount

    @kernel_function(name="Subtract")
    def subtract(
        self,
        input: Annotated[int | str, "The number to subtract from"],
        amount: Annotated[int | str, "The number to subtract"],
    ) -> Annotated[int, "The result"]:
        """Returns the difference of numbers provided."""
        if isinstance(input, str):
            input = int(input)
        if isinstance(amount, str):
            amount = int(amount)

        return input - amount
