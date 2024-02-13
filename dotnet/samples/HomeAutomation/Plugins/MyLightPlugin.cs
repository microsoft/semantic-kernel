// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using Microsoft.SemanticKernel;

namespace HomeAutomation.Plugins;

/// <summary>
/// Class that represents a controllable light.
/// </summary>
[Description("Represents a light")]
public class MyLightPlugin
{
    private bool _turnedOn;

    public MyLightPlugin(bool turnedOn = false)
    {
        _turnedOn = turnedOn;
    }

    [KernelFunction, Description("Returns whether this light is on")]
    public bool IsTurnedOn()
    {
        return _turnedOn;
    }

    [KernelFunction, Description("Turn on this light")]
    public void TurnOn()
    {
        _turnedOn = true;
    }

    [KernelFunction, Description("Turn off this light")]
    public void TurnOff()
    {
        _turnedOn = false;
    }
}
