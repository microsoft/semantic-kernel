from semantic_kernel.skill_definition import (
    sk_function,
    sk_function_context_parameter,
)
from semantic_kernel.orchestration.sk_context import SKContext

class ExactMatch:
    @sk_function(
        description="Check expected string with generated string if they match exactly",
        name="check_exact_match",
    )
    @sk_function_context_parameter(
        name="expected_str",
        description="A expected string to be compared with a generated string",
    )
    @sk_function_context_parameter(
        name="generated_str",
        description="A generated string to be compared with a expected string",
    )
    def check_exact_match(self, context: SKContext) -> str:
        expected_str = context["expected_str"]
        generated_str = context["generated_str"]

        matched = expected_str.strip().lower() == generated_str.strip().lower()

        return str(matched)
