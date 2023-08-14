import difflib
import re

from semantic_kernel.skill_definition import (
    sk_function,
    sk_function_context_parameter,
)
from semantic_kernel.orchestration.sk_context import SKContext


class StructuralSimiality:
    # Format SQL to check diff..
    def format_sql(sql):
        keywords = [
            "SELECT",
            "FROM",
            "WHERE",
            "ORDER BY",
            "OFFSET",
            "LIMIT",
            "JOIN",
            "CROSS JOIN",
            "INNER JOIN",
            "LEFT JOIN",
            "RIGHT JOIN",
            "ARRAY_CONTAINS",
            "AND",
            "OR",
        ]
        for keyword in keywords:
            sql = re.sub(
                r"\b" + re.escape(keyword) + r"\b",
                "\n" + keyword,
                sql,
                flags=re.IGNORECASE,
            )
        return sql

    @sk_function(
        description="Check if both result sets are matched.", name="compare_sql"
    )
    @sk_function_context_parameter(
        name="expected_str",
        description="A expected string to be compared with a generated string",
    )
    @sk_function_context_parameter(
        name="generated_str",
        description="A generated string to be compared with a expected string",
    )
    def compare_sql(self, context: SKContext) -> str:
        expected_sql = context["expected_str"]
        generated_sql = context["generated_str"]

        expected_sql = StructuralSimiality.format_sql(expected_sql)
        generated_sql = StructuralSimiality.format_sql(generated_sql)

        diff = difflib.unified_diff(
            expected_sql.strip().splitlines(),
            generated_sql.strip().splitlines(),
            lineterm="",
        )
        diff_string = "\n".join(diff)

        return diff_string
