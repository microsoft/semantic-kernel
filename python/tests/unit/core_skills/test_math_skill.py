# Copyright (c) Microsoft. All rights reserved.

import pytest

from semantic_kernel import Kernel
from semantic_kernel.core_skills import MathSkill
from semantic_kernel.orchestration.context_variables import ContextVariables


def test_can_be_instantiated():
    skill = MathSkill()
    assert skill is not None


def test_can_be_imported():
    kernel = Kernel()
    assert kernel.import_skill(MathSkill(), "math")
    assert kernel.skills.has_native_function("math", "add")
    assert kernel.skills.has_native_function("math", "subtract")


@pytest.mark.parametrize(
    "initial_Value, amount, expectedResult",
    [
        ("10", "10", "20"),
        ("0", "10", "10"),
        ("0", "-10", "-10"),
        ("10", "0", "10"),
        ("-1", "10", "9"),
        ("-10", "10", "0"),
        ("-192", "13", "-179"),
        ("-192", "-13", "-205"),
    ],
)
def test_add_when_valid_parameters_should_succeed(
    initial_Value, amount, expectedResult
):
    # Arrange
    context = ContextVariables()
    context["Amount"] = amount
    skill = MathSkill()

    # Act
    result = skill.add(initial_Value, context)

    # Assert
    assert result == expectedResult


@pytest.mark.parametrize(
    "initial_Value, amount, expectedResult",
    [
        ("10", "10", "0"),
        ("0", "10", "-10"),
        ("10", "0", "10"),
        ("100", "-10", "110"),
        ("100", "102", "-2"),
        ("-1", "10", "-11"),
        ("-10", "10", "-20"),
        ("-192", "13", "-205"),
    ],
)
def test_subtract_when_valid_parameters_should_succeed(
    initial_Value, amount, expectedResult
):
    # Arrange
    context = ContextVariables()
    context["Amount"] = amount
    skill = MathSkill()

    # Act
    result = skill.subtract(initial_Value, context)

    # Assert
    assert result == expectedResult


@pytest.mark.parametrize(
    "initial_Value",
    [
        "$0",
        "one hundred",
        "20..,,2,1",
        ".2,2.1",
        "0.1.0",
        "00-099",
        "¹²¹",
        "2²",
        "zero",
        "-100 units",
        "1 banana",
    ],
)
def test_add_when_invalid_initial_value_should_throw(initial_Value):
    # Arrange
    context = ContextVariables()
    context["Amount"] = "1"
    skill = MathSkill()

    # Act
    with pytest.raises(ValueError) as exception:
        skill.add(initial_Value, context)

    # Assert
    assert (
        str(exception.value)
        == f"Initial value provided is not in numeric format: {initial_Value}"
    )
    assert exception.type == ValueError


@pytest.mark.parametrize(
    "amount",
    [
        "$0",
        "one hundred",
        "20..,,2,1",
        ".2,2.1",
        "0.1.0",
        "00-099",
        "¹²¹",
        "2²",
        "zero",
        "-100 units",
        "1 banana",
    ],
)
def test_add_when_invalid_amount_should_throw(amount):
    # Arrange
    context = ContextVariables()
    context["Amount"] = amount
    skill = MathSkill()

    # Act / Assert
    with pytest.raises(ValueError) as exception:
        skill.add("1", context)

    assert (
        str(exception.value)
        == f"Context amount provided is not in numeric format: {amount}"
    )
    assert exception.type == ValueError


@pytest.mark.parametrize(
    "initial_value",
    [
        "$0",
        "one hundred",
        "20..,,2,1",
        ".2,2.1",
        "0.1.0",
        "00-099",
        "¹²¹",
        "2²",
        "zero",
        "-100 units",
        "1 banana",
    ],
)
def test_subtract_when_invalid_initial_value_should_throw(initial_value):
    # Arrange
    context = ContextVariables()
    context["Amount"] = "1"
    skill = MathSkill()

    # Act / Assert
    with pytest.raises(ValueError) as exception:
        skill.subtract(initial_value, context)

    # Assert
    assert (
        str(exception.value)
        == f"Initial value provided is not in numeric format: {initial_value}"
    )
    assert exception.type == ValueError


@pytest.mark.parametrize(
    "amount",
    [
        "$0",
        "one hundred",
        "20..,,2,1",
        ".2,2.1",
        "0.1.0",
        "00-099",
        "¹²¹",
        "2²",
        "zero",
        "-100 units",
        "1 banana",
    ],
)
def test_subtract_when_invalid_amount_should_throw(amount):
    # Arrange
    context = ContextVariables()
    context["Amount"] = amount
    skill = MathSkill()

    # Act / Assert
    with pytest.raises(ValueError) as exception:
        skill.subtract("1", context)

    # Assert
    assert (
        str(exception.value)
        == f"Context amount provided is not in numeric format: {amount}"
    )
    assert exception.type == ValueError
