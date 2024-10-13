# Copyright (c) Microsoft. All rights reserved.

import pytest

from semantic_kernel import Kernel
from semantic_kernel.core_plugins.math_plugin import MathPlugin
from semantic_kernel.functions.kernel_arguments import KernelArguments


def test_can_be_instantiated():
    plugin = MathPlugin()
    assert plugin is not None


def test_can_be_imported():
    kernel = Kernel()
    kernel.add_plugin(MathPlugin(), "math")
    assert kernel.get_plugin(plugin_name="math") is not None
    assert kernel.get_plugin(plugin_name="math").name == "math"
    assert kernel.get_function(plugin_name="math", function_name="Add") is not None
    assert kernel.get_function(plugin_name="math", function_name="Subtract") is not None


@pytest.mark.parametrize(
    "initial_value, amount, expected_result",
    [
        (10, 10, 20),
        (0, 10, 10),
        (0, -10, -10),
        (10, 0, 10),
        (-1, 10, 9),
        (-10, 10, 0),
        (-192, 13, -179),
        (-192, -13, -205),
    ],
)
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
def test_add_when_valid_parameters_should_succeed(
    initial_value, amount, expected_result
):
=======
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
def test_add_when_valid_parameters_should_succeed(
    initial_value, amount, expected_result
):
=======
<<<<<<< div
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
<<<<<<< Updated upstream
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< main
def test_add_when_valid_parameters_should_succeed(
    initial_value, amount, expected_result
):
=======
def test_add_when_valid_parameters_should_succeed(initial_value, amount, expected_result):
>>>>>>> ms/small_fixes
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    # Arrange
    plugin = MathPlugin()
    arguments = KernelArguments(input=initial_value, amount=amount)

    # Act
    result = plugin.add(**arguments)

    # Assert
    assert result == expected_result


@pytest.mark.parametrize(
    "initial_value, amount, expected_result",
    [
        (10, 10, 0),
        (0, 10, -10),
        (10, 0, 10),
        (100, -10, 110),
        (100, 102, -2),
        (-1, 10, -11),
        (-10, 10, -20),
        (-192, -13, -179),
    ],
)
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
<<<<<<< Updated upstream
>>>>>>> Stashed changes
def test_subtract_when_valid_parameters_should_succeed(
    initial_value, amount, expected_result
):
=======
<<<<<<< Updated upstream
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
=======
>>>>>>> Stashed changes
def test_subtract_when_valid_parameters_should_succeed(
    initial_value, amount, expected_result
):
=======
<<<<<<< div
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
<<<<<<< Updated upstream
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< main
def test_subtract_when_valid_parameters_should_succeed(
    initial_value, amount, expected_result
):
=======
def test_subtract_when_valid_parameters_should_succeed(initial_value, amount, expected_result):
>>>>>>> ms/small_fixes
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
    # Arrange
    plugin = MathPlugin()
    arguments = KernelArguments(input=initial_value, amount=amount)

    # Act
    result = plugin.subtract(**arguments)

    # Assert
    assert result == expected_result


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
def test_add_when_invalid_initial_value_should_throw(initial_value):
    # Arrange
    plugin = MathPlugin()
    arguments = KernelArguments(input=initial_value, amount=1)

    # Act
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    with pytest.raises(ValueError):
        plugin.add(**arguments)
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    with pytest.raises(ValueError):
        plugin.add(**arguments)
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
    with pytest.raises(ValueError):
        plugin.add(**arguments)
=======
>>>>>>> Stashed changes
=======
    with pytest.raises(ValueError):
        plugin.add(**arguments)
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< main
    with pytest.raises(ValueError):
        plugin.add(**arguments)
=======
    with pytest.raises(ValueError) as exception:
        plugin.add(**arguments)

    # Assert
    assert exception.type == ValueError
>>>>>>> ms/small_fixes
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head


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
    plugin = MathPlugin()
    arguments = KernelArguments(input=1, amount=amount)

    # Act / Assert
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    with pytest.raises(ValueError):
        plugin.add(**arguments)
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    with pytest.raises(ValueError):
        plugin.add(**arguments)
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
    with pytest.raises(ValueError):
        plugin.add(**arguments)
=======
>>>>>>> Stashed changes
=======
    with pytest.raises(ValueError):
        plugin.add(**arguments)
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< main
    with pytest.raises(ValueError):
        plugin.add(**arguments)
=======
    with pytest.raises(ValueError) as exception:
        plugin.add(**arguments)

    assert exception.type == ValueError
>>>>>>> ms/small_fixes
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head


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
    plugin = MathPlugin()
    arguments = KernelArguments(input=initial_value, amount=1)

    # Act / Assert
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    with pytest.raises(ValueError):
        plugin.subtract(**arguments)
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    with pytest.raises(ValueError):
        plugin.subtract(**arguments)
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
    with pytest.raises(ValueError):
        plugin.subtract(**arguments)
=======
>>>>>>> Stashed changes
=======
    with pytest.raises(ValueError):
        plugin.subtract(**arguments)
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< main
    with pytest.raises(ValueError):
        plugin.subtract(**arguments)
=======
    with pytest.raises(ValueError) as exception:
        plugin.subtract(**arguments)

    # Assert
    assert exception.type == ValueError
>>>>>>> ms/small_fixes
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head


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
    plugin = MathPlugin()
    arguments = KernelArguments(input=1, amount=amount)

    # Act / Assert
<<<<<<< HEAD
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
    with pytest.raises(ValueError):
        plugin.subtract(**arguments)
=======
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
<<<<<<< HEAD
    with pytest.raises(ValueError):
        plugin.subtract(**arguments)
=======
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
    with pytest.raises(ValueError):
        plugin.subtract(**arguments)
=======
>>>>>>> Stashed changes
=======
    with pytest.raises(ValueError):
        plugin.subtract(**arguments)
=======
>>>>>>> Stashed changes
>>>>>>> head
<<<<<<< main
    with pytest.raises(ValueError):
        plugin.subtract(**arguments)
=======
    with pytest.raises(ValueError) as exception:
        plugin.subtract(**arguments)

    # Assert
    assert exception.type == ValueError
>>>>>>> ms/small_fixes
<<<<<<< div
=======
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> head
<<<<<<< HEAD
>>>>>>> main
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
<<<<<<< Updated upstream
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> Stashed changes
=======
>>>>>>> eab985c52d058dc92abc75034bc790079131ce75
<<<<<<< div
=======
=======
>>>>>>> main
>>>>>>> Stashed changes
=======
>>>>>>> main
>>>>>>> Stashed changes
>>>>>>> head
