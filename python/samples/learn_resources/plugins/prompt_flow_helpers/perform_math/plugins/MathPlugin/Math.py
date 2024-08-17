# Copyright (c) Microsoft. All rights reserved.

import math

from semantic_kernel.orchestration.sk_context import SKContext
from semantic_kernel.skill_definition import sk_function, sk_function_context_parameter


class Math:
    @sk_function(
        description="Takes the square root of a number",
        name="Sqrt",
        input_description="The value to take the square root of",
    )
    def square_root(self, number: str) -> str:
        return str(math.sqrt(float(number)))

    @sk_function(
        description="Adds two numbers together",
        name="Add",
    )
    @sk_function_context_parameter(
        name="input",
        description="The first number to add",
    )
    @sk_function_context_parameter(
        name="number2",
        description="The second number to add",
    )
    def add(self, context: SKContext) -> str:
        return str(float(context["input"]) + float(context["number2"]))

    @sk_function(
        description="Subtract two numbers",
        name="Subtract",
    )
    @sk_function_context_parameter(
        name="input",
        description="The first number to subtract from",
    )
    @sk_function_context_parameter(
        name="number2",
        description="The second number to subtract away",
    )
    def subtract(self, context: SKContext) -> str:
        return str(float(context["input"]) - float(context["number2"]))

    @sk_function(
        description="Multiply two numbers. When increasing by a percentage, don't forget to add 1 to the percentage.",
        name="Multiply",
    )
    @sk_function_context_parameter(
        name="input",
        description="The first number to multiply",
    )
    @sk_function_context_parameter(
        name="number2",
        description="The second number to multiply",
    )
    def multiply(self, context: SKContext) -> str:
        return str(float(context["input"]) * float(context["number2"]))

    @sk_function(
        description="Divide two numbers",
        name="Divide",
    )
    @sk_function_context_parameter(
        name="input",
        description="The first number to divide from",
    )
    @sk_function_context_parameter(
        name="number2",
        description="The second number to divide by",
    )
    def divide(self, context: SKContext) -> str:
        return str(float(context["input"]) / float(context["number2"]))
