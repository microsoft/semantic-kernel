import semantic_kernel as sk
from semantic_kernel.core_skills.text_skill import TextSkill
from semantic_kernel.skill_definition.skill_collection import SkillCollection


def test_can_be_instantiated():
    assert TextSkill()


def test_can_be_imported():
    kernel = sk.Kernel()
    assert kernel.import_skill(TextSkill())
    assert kernel.skills.has_native_function(SkillCollection.GLOBAL_SKILL, "trim")


def test_can_be_imported_with_name():
    kernel = sk.Kernel()
    assert kernel.import_skill(TextSkill(), "text")
    assert kernel.skills.has_native_function("text", "trim")


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


def test_can_lower():
    text_skill = TextSkill()
    result = text_skill.lowercase("  HELLO WORLD  ")
    assert result == "  hello world  "


def test_can_upper():
    text_skill = TextSkill()
    result = text_skill.uppercase("  hello world  ")
    assert result == "  HELLO WORLD  "
