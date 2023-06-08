import pytest

from semantic_kernel.core_skills.wait_skill import WaitSkill

test_data_good = [
    "0",
    "1",
    "2.1",
    "0.1",
    "0.01",
    "0.001",
    "0.0001",
    "-0.0001",
    "-10000",
]

test_data_bad = [
    "$0",
    "one hundred",
    "20..,,2,1",
    ".2,2.1",
    "0.1.0",
    "00-099",
    "¹²¹",
    "2²",
    "zero",
    "-100 seconds",
    "1 second",
]


def test_can_be_instantiated():
    skill = WaitSkill()
    assert skill is not None


@pytest.mark.asyncio
@pytest.mark.parametrize("wait_time", test_data_good)
async def test_wait_valid_params(wait_time):
    skill = WaitSkill()

    await skill.wait(wait_time)

    assert True


@pytest.mark.asyncio
@pytest.mark.parametrize("wait_time", test_data_bad)
async def test_wait_invalid_params(wait_time):
    skill = WaitSkill()

    with pytest.raises(ValueError) as exc_info:
        await skill.wait("wait_time")

    assert exc_info.value.args[0] == "seconds text must be a number"
