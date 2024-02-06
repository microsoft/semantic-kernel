# Copyright (c) Microsoft. All rights reserved.
import typing as t

from semantic_kernel.kernel_pydantic import KernelBaseModel
from semantic_kernel.plugin_definition import kernel_function, kernel_function_context_parameter

if t.TYPE_CHECKING:
    from semantic_kernel.orchestration.kernel_context import KernelContext


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
        name="Amount",
        description="Amount to add",
        type="number",
        required=True,
    )
    def add(self, initial_value_text: str, context: "KernelContext") -> str:
        """
        Returns the Addition result of initial and amount values provided.

        :param initial_value_text: Initial value as string to add the specified amount
        :param context: Contains the context to get the numbers from
        :return: The resulting sum as a string
        """
        return MathPlugin.add_or_subtract(initial_value_text, context, add=True)

    @kernel_function(
        description="Subtracts value to a value",
        name="Subtract",
        input_description="The value to subtract",
    )
    @kernel_function_context_parameter(
        name="Amount",
        description="Amount to subtract",
        type="number",
        required=True,
    )
    def subtract(self, initial_value_text: str, context: "KernelContext") -> str:
        """
        Returns the difference of numbers provided.

        :param initial_value_text: Initial value as string to subtract the specified amount
        :param context: Contains the context to get the numbers from
        :return: The resulting subtraction as a string
        """
        return MathPlugin.add_or_subtract(initial_value_text, context, add=False)

    @staticmethod
    def add_or_subtract(initial_value_text: str, context: "KernelContext", add: bool) -> str:
        """
        Helper function to perform addition or subtraction based on the add flag.

        :param initial_value_text: Initial value as string to add or subtract the specified amount
        :param context: Contains the context to get the numbers from
        :param add: If True, performs addition, otherwise performs subtraction
        :return: The resulting sum or subtraction as a string
        """
        try:
            initial_value = int(initial_value_text)
        except ValueError:
            raise ValueError(f"Initial value provided is not in numeric format: {initial_value_text}")

        context_amount = context["Amount"]
        if context_amount is not None:
            try:
                amount = int(context_amount)
            except ValueError:
                raise ValueError("Context amount provided is not in numeric format:" f" {context_amount}")

            result = initial_value + amount if add else initial_value - amount
            return str(result)
        else:
            raise ValueError("Context amount should not be None.")
