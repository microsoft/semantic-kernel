# Copyright (c) Microsoft. All rights reserved.

import json
import pytest

from samples.concepts.react.azure_ai_react_agent import (
    CalculatorPlugin,
    WeatherPlugin,
    extract_function_descriptions,
    parse_action_from_response,
)


class TestCalculatorPlugin:
    """Test the CalculatorPlugin functionality."""

    def test_add_valid_numbers(self):
        """Test adding two valid numbers."""
        plugin = CalculatorPlugin()
        result = plugin.add("5", "3")
        assert result == "8.0"

    def test_add_invalid_numbers(self):
        """Test adding invalid number formats."""
        plugin = CalculatorPlugin()
        result = plugin.add("invalid", "3")
        assert result == "Error: Invalid number format"

    def test_multiply_valid_numbers(self):
        """Test multiplying two valid numbers."""
        plugin = CalculatorPlugin()
        result = plugin.multiply("4", "7")
        assert result == "28.0"

    def test_multiply_invalid_numbers(self):
        """Test multiplying invalid number formats."""
        plugin = CalculatorPlugin()
        result = plugin.multiply("abc", "def")
        assert result == "Error: Invalid number format"

    def test_divide_valid_numbers(self):
        """Test dividing two valid numbers."""
        plugin = CalculatorPlugin()
        result = plugin.divide("10", "2")
        assert result == "5.0"

    def test_divide_by_zero(self):
        """Test division by zero handling."""
        plugin = CalculatorPlugin()
        result = plugin.divide("10", "0")
        assert result == "Error: Division by zero"

    def test_divide_invalid_numbers(self):
        """Test dividing invalid number formats."""
        plugin = CalculatorPlugin()
        result = plugin.divide("10", "invalid")
        assert result == "Error: Invalid number format"


class TestWeatherPlugin:
    """Test the WeatherPlugin functionality."""

    def test_get_weather_known_city(self):
        """Test getting weather for a known city."""
        plugin = WeatherPlugin()
        result = plugin.get_weather("Istanbul")
        assert "Istanbul" in result
        assert "Sunny, 22°C" in result

    def test_get_weather_case_insensitive(self):
        """Test getting weather with case insensitive city names."""
        plugin = WeatherPlugin()
        result = plugin.get_weather("ISTANBUL")
        assert "ISTANBUL" in result
        assert "Sunny, 22°C" in result

    def test_get_weather_unknown_city(self):
        """Test getting weather for an unknown city."""
        plugin = WeatherPlugin()
        result = plugin.get_weather("UnknownCity")
        assert "not available" in result
        assert "UnknownCity" in result


class TestActionParsing:
    """Test the action parsing functionality."""

    def test_parse_valid_action_with_code_blocks(self):
        """Test parsing a valid action JSON in code blocks."""
        response = """
        I need to add two numbers.
        
        ```
        {
          "action": "CalculatorPlugin.add",
          "action_variables": {"number1": "5", "number2": "3"}
        }
        ```
        """

        action_name, action_variables = parse_action_from_response(response)

        assert action_name == "CalculatorPlugin.add"
        assert action_variables == {"number1": "5", "number2": "3"}

    def test_parse_valid_action_without_code_blocks(self):
        """Test parsing a valid action JSON without code blocks."""
        response = """
        I need to multiply two numbers.
        {"action": "CalculatorPlugin.multiply", "action_variables": {"number1": "4", "number2": "7"}}
        """

        action_name, action_variables = parse_action_from_response(response)

        assert action_name == "CalculatorPlugin.multiply"
        assert action_variables == {"number1": "4", "number2": "7"}

    def test_parse_invalid_json(self):
        """Test parsing response with invalid JSON."""
        response = """
        This is not a valid JSON action.
        {invalid json}
        """

        action_name, action_variables = parse_action_from_response(response)

        assert action_name is None
        assert action_variables == {}

    def test_parse_no_action_in_response(self):
        """Test parsing response with no action."""
        response = """
        This is just a regular response without any action.
        """

        action_name, action_variables = parse_action_from_response(response)

        assert action_name is None
        assert action_variables == {}

    def test_parse_action_missing_variables(self):
        """Test parsing action with missing action_variables."""
        response = """
        ```
        {
          "action": "CalculatorPlugin.add"
        }
        ```
        """

        action_name, action_variables = parse_action_from_response(response)

        assert action_name == "CalculatorPlugin.add"
        assert action_variables == {}


class TestFunctionDescriptions:
    """Test function description extraction."""

    def test_extract_function_descriptions_with_mock_kernel(self):
        """Test extracting function descriptions from a mock kernel."""

        # Create a mock kernel-like structure
        class MockFunction:
            def __init__(self, name, description, parameters):
                self.name = name
                self.metadata = MockMetadata(description, parameters)

        class MockMetadata:
            def __init__(self, description, parameters):
                self.description = description
                self.parameters = parameters

        class MockParameter:
            def __init__(self, name, description):
                self.name = name
                self.description = description

        class MockPlugin:
            def __init__(self, functions):
                self._functions = functions

            def items(self):
                return self._functions.items()

        class MockKernel:
            def __init__(self):
                self.plugins = {
                    "CalculatorPlugin": MockPlugin(
                        {
                            "add": MockFunction(
                                "add",
                                "Adds two numbers together.",
                                [
                                    MockParameter("number1", "The first number"),
                                    MockParameter("number2", "The second number"),
                                ],
                            )
                        }
                    )
                }

        mock_kernel = MockKernel()
        result = extract_function_descriptions(mock_kernel)  # type: ignore

        assert "CalculatorPlugin.add: Adds two numbers together." in result
        assert "- number1: The first number" in result
        assert "- number2: The second number" in result


class TestReactPatternComponents:
    """Test React pattern specific components."""

    def test_react_prompt_template_constants(self):
        """Test that the React prompt template contains required sections."""
        from samples.concepts.react.azure_ai_react_agent import REACT_PROMPT_TEMPLATE

        # Check for key React pattern elements
        assert "[THOUGHT]" in REACT_PROMPT_TEMPLATE
        assert "[ACTION]" in REACT_PROMPT_TEMPLATE
        assert "[OBSERVATION]" in REACT_PROMPT_TEMPLATE
        assert "[FINAL ANSWER]" in REACT_PROMPT_TEMPLATE
        assert "{{$question}}" in REACT_PROMPT_TEMPLATE
        assert "{{$function_descriptions}}" in REACT_PROMPT_TEMPLATE
        assert "{{$agent_scratchpad}}" in REACT_PROMPT_TEMPLATE

    def test_react_prompt_template_json_example(self):
        """Test that the prompt template includes JSON action example."""
        from samples.concepts.react.azure_ai_react_agent import REACT_PROMPT_TEMPLATE

        assert '"action":' in REACT_PROMPT_TEMPLATE
        assert '"action_variables":' in REACT_PROMPT_TEMPLATE
        assert "CalculatorPlugin.Add" in REACT_PROMPT_TEMPLATE


if __name__ == "__main__":
    pytest.main([__file__])
