// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using Microsoft.SemanticKernel;

namespace OpenAIFunctionCalling.Plugins;

/// <summary>
/// Class that represents a controllable light bulb.
/// </summary>
[Description("Represents a light bulb")]
public class MyLightPlugin(bool turnedOn = false)
{
    private bool _turnedOn = turnedOn;

    [KernelFunction]
    [Description("Returns whether this light is on")]
    public bool IsTurnedOn() => this._turnedOn;

    [KernelFunction]
    [Description("Turn on this light")]
    public void TurnOn() => this._turnedOn = true;

    [KernelFunction]
    [Description("Turn off this light")]
    public void TurnOff() => this._turnedOn = false;
}
