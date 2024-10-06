# Copyright (c) Microsoft. All rights reserved.
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream

from typing import Annotated
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD

from typing import Annotated
=======
<<<<<<< main

from typing import Annotated
=======
import sys

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated
>>>>>>> ms/small_fixes
>>>>>>> main
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

from semantic_kernel.functions.kernel_function_decorator import kernel_function


class MathPlugin:
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    """Description: MathPlugin provides a set of functions to make Math calculations.
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    """Description: MathPlugin provides a set of functions to make Math calculations.
=======
<<<<<<< main
    """Description: MathPlugin provides a set of functions to make Math calculations.
=======
    """
    Description: MathPlugin provides a set of functions to make Math calculations.
>>>>>>> ms/small_fixes
>>>>>>> main
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

    Usage:
        kernel.add_plugin(MathPlugin(), plugin_name="math")

    Examples:
        {{math.Add}} => Returns the sum of input and amount (provided in the KernelArguments)
        {{math.Subtract}} => Returns the difference of input and amount (provided in the KernelArguments)
    """

    @kernel_function(name="Add")
    def add(
        self,
        input: Annotated[int, "the first number to add"],
        amount: Annotated[int, "the second number to add"],
    ) -> Annotated[int, "the output is a number"]:
        """Returns the Addition result of the values provided."""
        if isinstance(input, str):
            input = int(input)
        if isinstance(amount, str):
            amount = int(amount)
        return MathPlugin.add_or_subtract(input, amount, add=True)

<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    @kernel_function(name="Subtract")
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    @kernel_function(name="Subtract")
=======
<<<<<<< main
    @kernel_function(name="Subtract")
=======
    @kernel_function(
        description="Subtracts value to a value",
        name="Subtract",
    )
>>>>>>> ms/small_fixes
>>>>>>> main
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
    def subtract(
        self,
        input: Annotated[int, "the first number"],
        amount: Annotated[int, "the number to subtract"],
    ) -> int:
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        """Returns the difference of numbers provided."""
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        """Returns the difference of numbers provided."""
=======
<<<<<<< main
        """Returns the difference of numbers provided."""
=======
        """
        Returns the difference of numbers provided.

        :param initial_value_text: Initial value as string to subtract the specified amount
        :param context: Contains the context to get the numbers from
        :return: The resulting subtraction as a string
        """
>>>>>>> ms/small_fixes
>>>>>>> main
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
        if isinstance(input, str):
            input = int(input)
        if isinstance(amount, str):
            amount = int(amount)
        return MathPlugin.add_or_subtract(input, amount, add=False)

    @staticmethod
    def add_or_subtract(input: int, amount: int, add: bool) -> int:
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
        """Helper function to perform addition or subtraction based on the add flag."""
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
        """Helper function to perform addition or subtraction based on the add flag."""
=======
<<<<<<< main
        """Helper function to perform addition or subtraction based on the add flag."""
=======
        """
        Helper function to perform addition or subtraction based on the add flag.

        :param initial_value_text: Initial value as string to add or subtract the specified amount
        :param context: Contains the context to get the numbers from
        :param add: If True, performs addition, otherwise performs subtraction
        :return: The resulting sum or subtraction as a string
        """
>>>>>>> ms/small_fixes
>>>>>>> main
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
        return input + amount if add else input - amount
