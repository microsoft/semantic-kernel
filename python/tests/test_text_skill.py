

import semantic_kernel as sk
import asyncio
from semantic_kernel.core_skills.text_skill import TextSkill
from semantic_kernel.skill_definition.skill_collection import SkillCollection


def test_can_be_instantiated():
    assert TextSkill()


def test_can_be_imported():
    kernel = sk.create_kernel()
    assert kernel.import_skill(TextSkill)
    assert kernel.skills.has_native_function(SkillCollection.GLOBAL_SKILL, 'trim')


def test_works_in_prompt():
    kernel = sk.create_kernel()
    kernel.config.add_openai_completion_backend(
        "davinci-003", "text-davinci-003", "123", "12"
    )
    kernel.import_skill(TextSkill, 'text')

    trim_function = sk.extensions.create_semantic_function(
        kernel, "{{text.trim $input}}", max_tokens=200, temperature=0, top_p=0.5
    )
    result = asyncio.run(kernel.run_on_str_async('  hello  world  ', trim_function))
    result = str(result.result)
    assert result == "hello world"


def test_can_trim():

    result = TextSkill.trim("  hello world  ")
    assert result == "hello world"


def test_can_trim_start():

    result = TextSkill.trim_start("  hello world  ")
    assert result == "hello world  "


def test_can_trim_end():

    result = TextSkill.trim_end("  hello world  ")
    assert result == "  hello world"
