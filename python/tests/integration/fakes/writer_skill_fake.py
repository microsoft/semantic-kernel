from semantic_kernel.skill_definition.sk_function_decorator import sk_function


class WriterSkillFake:
    @sk_function(
        description="Translate",
        name="Translate",
    )
    def translate(self, language: str) -> str:
        return f"Translate: {language}"

    @sk_function(description="Write an outline for a novel", name="NovelOutline")
    def write_novel_outline(self, input: str) -> str:
        return f"Novel outline: {input}"
