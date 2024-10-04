// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using Microsoft.SemanticKernel;

namespace HomeAutomation.Plugins;

/// <summary>
/// Simple plugin to illustrate creating plugins which have dependencies
/// that can be resolved through dependency injection.
/// </summary>
public class MyAlarmPlugin
{
    private readonly MyTimePlugin _timePlugin;

    public MyAlarmPlugin(MyTimePlugin timePlugin)
    {
        _timePlugin = timePlugin;
    }

    [KernelFunction, Description("Sets an alarm at the provided time")]
    public void SetAlarm(string _)
    {
        // Code to actually set the alarm would be placed here
    }
}
