

import semantic_kernel as sk
import asyncio
from semantic_kernel.core_skills.text_skill import TextSkill
from semantic_kernel.skill_definition.skill_collection import SkillCollection


def test_can_be_instantiated():
    assert TextSkill()


def test_can_be_imported():
    kernel = sk.create_kernel()
    assert kernel.import_skill(TextSkill())
    assert kernel.skills.has_native_function(SkillCollection.GLOBAL_SKILL, 'trim')


def test_can_trim():
    text_skill = TextSkill()
    result = text_skill.trim("  hello world  ")
    assert result == "hello world"


def test_can_trim_start():
    text_skill = TextSkill()
    result = text_skill.trim_start("  hello world  ")
    assert result == "hello world  "


def test_can_trim_end():
    text_skill = TextSkill()
    result = text_skill.trim_end("  hello world  ")
    assert result == "  hello world"
