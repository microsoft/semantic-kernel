// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using Microsoft.SemanticKernel;

namespace OpenAIFunctionCalling.Plugins;

/// <summary>
/// Class that represents a controllable alarm.
/// </summary>
public class MyAlarmPlugin
{
    private string _hour;

    public MyAlarmPlugin(string providedHour)
    {
        this._hour = providedHour;
    }

    [KernelFunction]
    [Description("Sets an alarm at the provided time")]
    public string SetAlarm(string time)
    {
        this._hour = time;
        return this.GetCurrentAlarm();
    }

    [KernelFunction]
    [Description("Get current alarm set")]
    public string GetCurrentAlarm()
    {
        return $"Alarm set for {this._hour}";
    }
}
