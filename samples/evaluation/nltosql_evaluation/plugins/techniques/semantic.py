import sqlparse

from semantic_kernel.skill_definition import (
    sk_function,
    sk_function_context_parameter,
)
from semantic_kernel.orchestration.sk_context import SKContext


class SemanticAccuracy:
    @sk_function(
        description="Check if both result sets are matched.", name="check_result_match"
    )
    @sk_function_context_parameter(
        name="expected_result", description="1st result set list to be compared"
    )
    @sk_function_context_parameter(
        name="generated_result", description="2nd result set list to be compared"
    )
    def check_result_match(self, context: SKContext) -> str:
        expected_result = context["expected_result"]
        generated_result = context["generated_result"]

        # print("expected_result=", expected_result)
        # print("generated_result=", generated_result)

        matched = "True"

        # 1. compare size..
        if len(expected_result) != len(generated_result):
            # print("row counts are not same =", len(expected_result))
            matched = "False"
        else:
            # 2. compare row
            for inx in range(len(expected_result)):
                if expected_result[inx] != generated_result[inx]:
                    matched = "False"
                    break

        return matched