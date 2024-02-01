# Copyright (c) Microsoft. All rights reserved.

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.plugin_definition import kernel_function, kernel_function_context_parameter


class MathPlugin(KernelBaseModel):
    """
    Description: MathPlugin provides a set of functions to make Math calculations.

    Usage:
        kernel.import_plugin(MathPlugin(), plugin_name="math")

    Examples:
        {{math.Add}}         => Returns the sum of initial_value_text and Amount (provided in the KernelContext)
    """

    @kernel_function(
        description="Adds value to a value",
        name="Add",
        input_description="The value to add",
    )
    @kernel_function_context_parameter(
        name="amount",
        description="Amount to add",
        type="number",
        required=True,
    )
    @staticmethod
    def add(input: int, amount: int) -> int:
        """
        Returns the Addition result of initial and amount values provided.

        :param initial_value_text: Initial value as string to add the specified amount
        :param context: Contains the context to get the numbers from
        :return: The resulting sum as a string
        """
        return MathPlugin.add_or_subtract(input, amount, add=True)

    @kernel_function(
        description="Subtracts value to a value",
        name="Subtract",
        input_description="The value to subtract",
    )
    @kernel_function_context_parameter(
        name="amount",
        description="Amount to subtract",
        type="number",
        required=True,
    )
    @staticmethod
    def subtract(input: int, amount: int) -> int:
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
