// Copyright (c) Microsoft. All rights reserved.

namespace AotCompatibility.TestApp.Plugins;

internal sealed class Weather
{
    public int? Temperature { get; set; }
    public string? Condition { get; set; }

    public override string ToString() => $"Current weather(temperature: {this.Temperature}F, condition: {this.Condition})";
}
