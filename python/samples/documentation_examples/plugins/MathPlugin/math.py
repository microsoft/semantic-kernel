import math
import sys

if sys.version_info >= (3, 9):
    from typing import Annotated
else:
    from typing_extensions import Annotated

from semantic_kernel.functions.kernel_function_decorator import kernel_function


class Math:
    """
    Description: MathPlugin provides a set of functions to make Math calculations.

    Usage:
        kernel.import_plugin_from_object(MathPlugin(), plugin_name="math")

    Examples:
        {{math.Add}} => Returns the sum of input and amount (provided in the KernelArguments)
        {{math.Subtract}} => Returns the difference of input and amount (provided in the KernelArguments)
        {{math.Multiply}} => Returns the multiplication of input and number2 (provided in the KernelArguments)
        {{math.Divide}} => Returns the division of input and number2 (provided in the KernelArguments)
    """

    @kernel_function(
        description="Divide two numbers.",
        name="Divide",
    )
    def divide(
        self,
        input: Annotated[int, "the first number to divide from"],
        number2: Annotated[int, "the second number to by"],
    ) -> Annotated[str, "The output is a string"]:
        return str(float(input) / float(number2))

    @kernel_function(
        description="Multiply two numbers. When increasing by a percentage, don't forget to add 1 to the percentage.",
        name="Multiply",
    )
    def multiply(
        self,
        input: Annotated[int, "the first number to multiply"],
        number2: Annotated[int, "the second number to multiply"],
    ) -> Annotated[str, "The output is a string"]:
        return str(float(input) * float(number2))

    @kernel_function(
        description="Takes the square root of a number",
        name="Sqrt",
    )
    def square_root(
        self,
        number: Annotated[str, "the number to take the square root of"],
    ) -> Annotated[str, "The output is a string"]:
        return str(math.sqrt(float(number)))

    @kernel_function(name="Add")
    def add(
        self,
        input: Annotated[float, "the first number to add"],
        amount: Annotated[float, "the second number to add"],
    ) -> Annotated[float, "the output is a number"]:
        """Returns the Addition result of the values provided."""
        if isinstance(input, str):
            input = float(input)
        if isinstance(amount, str):
            amount = float(amount)
        return Math.add_or_subtract(input, amount, add=True)

    @kernel_function(
        description="Subtracts value to a value",
        name="Subtract",
    )
    def subtract(
        self,
        input: Annotated[float, "the first number"],
        amount: Annotated[float, "the number to subtract"],
    ) -> float:
        """
        Returns the difference of numbers provided.

        :param initial_value_text: Initial value as string to subtract the specified amount
        :param context: Contains the context to get the numbers from
        :return: The resulting subtraction as a string
        """
        if isinstance(input, str):
            input = float(input)
        if isinstance(amount, str):
            amount = float(amount)
        return Math.add_or_subtract(input, amount, add=False)

    @staticmethod
    def add_or_subtract(input: float, amount: float, add: bool) -> float:
        """
        Helper function to perform addition or subtraction based on the add flag.

        :param initial_value_text: Initial value as string to add or subtract the specified amount
        :param context: Contains the context to get the numbers from
        :param add: If True, performs addition, otherwise performs subtraction
        :return: The resulting sum or subtraction as a string
        """
        return input + amount if add else input - amount
