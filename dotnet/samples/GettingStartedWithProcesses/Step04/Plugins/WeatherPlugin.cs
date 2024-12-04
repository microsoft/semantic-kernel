// Copyright (c) Microsoft. All rights reserved.
using System.ComponentModel;
using Microsoft.SemanticKernel;

namespace Step04.Plugins;

internal sealed record WeatherForecast(
    string Date,
    string Location,
    string HighTemperature,
    string LowTemperature,
    string Precipition);

/// <summary>
/// Mock plug-in to provide weather information.
/// </summary>
internal sealed class WeatherPlugin
{
    private readonly Dictionary<string, WeatherForecast> _forecasts = [];

    [KernelFunction]
    public string GetCurrentDate() => DateTime.Now.Date.ToString("dd-MMM-yyyy");

    [KernelFunction]
    [Description("Provide the weather forecast for the given date and location.  Dates farther than 15 days out will use historical data.")]
    public WeatherForecast GetForecast(
        string date,
        string location)
    {
        string key = $"{date}-{location}";

        if (!this._forecasts.TryGetValue(key, out WeatherForecast? forecast))
        {
            forecast = GenerateForecast(date, location);
            this._forecasts[key] = forecast;
        }

        return forecast;
    }

    private static WeatherForecast GenerateForecast(string date, string location)
    {
        int highTemp = Random.Shared.Next(49, 96);
        int lowTemp = highTemp - Random.Shared.Next(12, 20);
        int precip = Random.Shared.Next(0, 80);

        return
            new WeatherForecast(
                date,
                location,
                $"{highTemp} F",
                $"{lowTemp} F",
                $"{precip} %");
    }
}
