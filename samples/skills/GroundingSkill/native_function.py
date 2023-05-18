from semantic_kernel.skill_definition import sk_function


class PythonGroundingSkill:
    @sk_function(
        description="Extract contents of <json_block> tags",
        name="ExtractJsonBlock",
    )
    def extract_json_block_from_text(self, text: str) -> str:
        start_tag = "<json_block>"
        end_tag = "</json_block>"
        i_0 = text.find(start_tag) + len(start_tag)
        i_1 = text.find(end_tag)

        extracted_text = text[i_0:i_1]

        return extracted_text
