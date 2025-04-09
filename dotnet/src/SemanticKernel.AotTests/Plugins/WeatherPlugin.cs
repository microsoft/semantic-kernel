// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using Microsoft.SemanticKernel;

namespace SemanticKernel.AotTests.Plugins;
internal sealed class WeatherPlugin
{
    [KernelFunction]
    [Description("Get the current weather in a given location.")]
    public Weather GetCurrentWeather(Location location)
    {
        return location.City switch
        {
            "Boston" => new Weather { Temperature = 61, Condition = "rainy" },
            "London" => new Weather { Temperature = 55, Condition = "cloudy" },
            "Miami" => new Weather { Temperature = 80, Condition = "sunny" },
            "Tokyo" => new Weather { Temperature = 50, Condition = "sunny" },
            "Sydney" => new Weather { Temperature = 75, Condition = "sunny" },
            _ => new Weather { Temperature = 31, Condition = "snowing" }
        };
    }
}
