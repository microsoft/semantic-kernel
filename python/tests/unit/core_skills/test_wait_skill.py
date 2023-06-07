import pytest

from semantic_kernel.core_skills.wait_skill import WaitSkill


def test_can_be_instantiated():
    skill = WaitSkill()
    assert skill is not None


@pytest.mark.asyncio
async def test_can_wait():
    skill = WaitSkill()

    await skill.wait("0.1")

    assert True
