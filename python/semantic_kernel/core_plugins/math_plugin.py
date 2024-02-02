# Copyright (c) Microsoft. All rights reserved.

from typing import Annotated, AsyncIterable, Optional

from semantic_kernel.plugin_definition import kernel_function


class MathPlugin:
    """
    Description: MathPlugin provides a set of functions to make Math calculations.

    Usage:
        kernel.import_plugin(MathPlugin(), plugin_name="math")

    Examples:
        {{math.Add}}         => Returns the sum of initial_value_text and Amount (provided in the KernelContext)
    """

    @kernel_function()
    def add(
        self,
        input: Annotated[int, "the first number to add"],
        amount: Annotated[int, "the second number to add"],
    ) -> Annotated[int, "the output is a number"]:
        """Returns the Addition result of the values provided."""
        return MathPlugin.add_or_subtract(input, amount, add=True)

    @kernel_function()
    async def stream_add(
        self,
        input: Annotated[int, "the first number to add"],
        amount: Annotated[Optional[int], "the second number to add, default is 5"] = 5,
    ) -> Annotated[AsyncIterable[int], "the output is stream of numbers"]:
        """Streams the Addition result of the values provided."""
        yield MathPlugin.add_or_subtract(input, amount, add=True)

    @kernel_function(
        description="Subtracts value to a value",
        name="Subtract",
    )
    def subtract(self, input: int, amount: int) -> int:
        """
        Returns the difference of numbers provided.

        :param initial_value_text: Initial value as string to subtract the specified amount
        :param context: Contains the context to get the numbers from
        :return: The resulting subtraction as a string
        """
        return MathPlugin.add_or_subtract(input, amount, add=False)

    @staticmethod
    def add_or_subtract(input: int, amount: int, add: bool) -> int:
        """
        Helper function to perform addition or subtraction based on the add flag.

        :param initial_value_text: Initial value as string to add or subtract the specified amount
        :param context: Contains the context to get the numbers from
        :param add: If True, performs addition, otherwise performs subtraction
        :return: The resulting sum or subtraction as a string
        """
        return input + amount if add else input - amount
