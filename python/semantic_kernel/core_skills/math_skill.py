# Copyright (c) Microsoft. All rights reserved.
import typing as t

from semantic_kernel.sk_pydantic import PydanticField
from semantic_kernel.skill_definition import sk_function, sk_function_context_parameter

if t.TYPE_CHECKING:
    from semantic_kernel.orchestration.sk_context import SKContext


class MathSkill(PydanticField):
    """
    Description: MathSkill provides a set of functions to make Math calculations.

    Usage:
        kernel.import_skill(MathSkill(), skill_name="math")

    Examples:
        {{math.Add}}         => Returns the sum of initial_value_text and Amount (provided in the SKContext)
    """

    @sk_function(
        description="Adds value to a value",
        name="Add",
        input_description="The value to add",
    )
    @sk_function_context_parameter(
        name="Amount",
        description="Amount to add",
    )
    def add(self, initial_value_text: str, context: "SKContext") -> str:
        """
        Returns the Addition result of initial and amount values provided.

        :param initial_value_text: Initial value as string to add the specified amount
        :param context: Contains the context to get the numbers from
        :return: The resulting sum as a string
        """
        return MathSkill.add_or_subtract(initial_value_text, context, add=True)

    @sk_function(
        description="Subtracts value to a value",
        name="Subtract",
        input_description="The value to subtract",
    )
    @sk_function_context_parameter(
        name="Amount",
        description="Amount to subtract",
    )
    def subtract(self, initial_value_text: str, context: "SKContext") -> str:
        """
        Returns the difference of numbers provided.

        :param initial_value_text: Initial value as string to subtract the specified amount
        :param context: Contains the context to get the numbers from
        :return: The resulting subtraction as a string
        """
        return MathSkill.add_or_subtract(initial_value_text, context, add=False)

    @staticmethod
    def add_or_subtract(
        initial_value_text: str, context: "SKContext", add: bool
    ) -> str:
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
            raise ValueError(
                f"Initial value provided is not in numeric format: {initial_value_text}"
            )

        context_amount = context["Amount"]
        if context_amount is not None:
            try:
                amount = int(context_amount)
            except ValueError:
                raise ValueError(
                    "Context amount provided is not in numeric format:"
                    f" {context_amount}"
                )

            result = initial_value + amount if add else initial_value - amount
            return str(result)
        else:
            raise ValueError("Context amount should not be None.")
