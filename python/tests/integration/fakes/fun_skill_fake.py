from semantic_kernel.skill_definition.sk_function_decorator import sk_function


class FunSkillFake:
    @sk_function(
        description="Write a joke",
        name="WriteJoke",
    )
    def write_joke(self) -> str:
        return "WriteJoke"
