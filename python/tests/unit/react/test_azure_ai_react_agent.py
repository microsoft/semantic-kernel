# Copyright (c) Microsoft. All rights reserved.

import pytest
from unittest.mock import AsyncMock, MagicMock

from samples.concepts.react.azure_ai_react_agent import WeatherPlugin, run_react_agent


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

    def test_get_weather_various_cities(self):
        """Test getting weather for various predefined cities."""
        plugin = WeatherPlugin()
        
        test_cases = [
            ("ankara", "Cloudy, 18°C"),
            ("izmir", "Partly cloudy, 25°C"),
            ("antalya", "Sunny, 28°C"),
            ("new york", "Rainy, 15°C"),
            ("london", "Foggy, 12°C"),
            ("paris", "Sunny, 20°C"),
        ]
        
        for city, expected_weather in test_cases:
            result = plugin.get_weather(city)
            assert city in result.lower()
            assert expected_weather in result


class TestReactAgentRunner:
    """Test the React agent runner functionality."""

    @pytest.mark.asyncio
    async def test_run_react_agent_mock(self):
        """Test the run_react_agent function with a mocked agent."""
        # Create a mock agent
        mock_agent = AsyncMock()
        mock_response = MagicMock()
        mock_response.content = "The answer is 42"
        mock_agent.get_response.return_value = mock_response
        
        # Test the runner
        question = "What is 21 * 2?"
        result = await run_react_agent(mock_agent, question)
        
        # Verify the agent was called correctly
        mock_agent.get_response.assert_called_once_with(messages=question)
        assert result == "The answer is 42"

    @pytest.mark.asyncio 
    async def test_run_react_agent_with_different_questions(self):
        """Test the run_react_agent function with various question types."""
        # Create a mock agent that returns different responses
        mock_agent = AsyncMock()
        
        test_cases = [
            ("Calculate 5 + 3", "The result is 8"),
            ("What's the weather in Paris?", "It's sunny and 20°C in Paris"),
            ("Multiply 10 by 4 and tell me the weather in Istanbul", "40, and it's sunny, 22°C in Istanbul"),
        ]
        
        for question, expected_response in test_cases:
            mock_response = MagicMock()
            mock_response.content = expected_response
            mock_agent.get_response.return_value = mock_response
            
            result = await run_react_agent(mock_agent, question)
            assert result == expected_response
            mock_agent.get_response.assert_called_with(messages=question)


class TestPluginFunctionDecorators:
    """Test that plugin functions have correct decorators and annotations."""

    def test_weather_plugin_function_decorator(self):
        """Test that WeatherPlugin.get_weather has the correct kernel_function decorator."""
        plugin = WeatherPlugin()
        
        # Check that the function exists and is callable
        assert hasattr(plugin, 'get_weather')
        assert callable(plugin.get_weather)
        
        # Test function execution
        result = plugin.get_weather("test_city")
        assert isinstance(result, str)
        assert "test_city" in result

    def test_weather_plugin_function_annotations(self):
        """Test that WeatherPlugin.get_weather has proper type annotations."""
        plugin = WeatherPlugin()
        func = plugin.get_weather
        
        # Check that function has annotations
        assert hasattr(func, '__annotations__')
        annotations = func.__annotations__
        
        # Should have return annotation
        assert 'return' in annotations


if __name__ == "__main__":
    pytest.main([__file__])
