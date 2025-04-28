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
    /// <returns>The current weather for the specified city.</returns>
    [KernelFunction, Description("Gets the current weather for the specified city and specified date time.")]
    public static async Task<string> GetWeatherForCityAsync(string cityName)
    {
        using var client = new HttpClient();

        return await client.GetStringAsync(new Uri($"https://wttr.in/{cityName}?format=j1"));
    }
}
