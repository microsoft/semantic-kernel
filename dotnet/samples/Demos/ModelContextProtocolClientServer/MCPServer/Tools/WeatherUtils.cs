// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using Microsoft.SemanticKernel;

namespace MCPServer.Tools;

/// <summary>
/// A collection of utility methods for working with weather.
/// </summary>
internal sealed class WeatherUtils
{
    /// <summary>
    /// Gets the current weather for the specified city.
    /// </summary>
    /// <param name="cityName">The name of the city.</param>
    /// <param name="currentDateTimeInUtc">The current date time in UTC.</param>
    /// <returns>The current weather for the specified city.</returns>
    [KernelFunction, Description("Gets the current weather for the specified city and specified date time.")]
    public static string GetWeatherForCity(string cityName, string currentDateTimeInUtc)
    {
        return cityName switch
        {
            "Boston" => "61 and rainy",
            "London" => "55 and cloudy",
            "Miami" => "80 and sunny",
            "Paris" => "60 and rainy",
            "Tokyo" => "50 and sunny",
            "Sydney" => "75 and sunny",
            "Tel Aviv" => "80 and sunny",
            _ => "31 and snowing",
        };
    }
}
