// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable IDE0005 // Using directive is unnecessary

using System.ComponentModel;
using Microsoft.SemanticKernel;

#pragma warning restore IDE0005 // Using directive is unnecessary

namespace StepwisePlannerMigration.Plugins;

/// <summary>
/// Sample plugin which provides fake weather information.
/// </summary>
public sealed class WeatherPlugin
{
    [KernelFunction]
    [Description("Gets the current weather for the specified city")]
    public string GetWeatherForCity(string cityName) =>
        cityName switch
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
