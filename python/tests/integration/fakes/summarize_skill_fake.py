from semantic_kernel.skill_definition.sk_function_decorator import sk_function


class SummarizeSkillFake:
    @sk_function(
        description="Summarize",
        name="Summarize",
    )
    def translate(self) -> str:
        return "Summarize"
