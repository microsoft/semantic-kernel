// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using Microsoft.SemanticKernel;

/// <summary>
/// Class that represents a controllable alarm.
/// </summary>
public class MyAlarmPlugin
{
    private string hour;

    public MyAlarmPlugin(string providedHour)
    {
        this.hour = providedHour;
    }

    [KernelFunction, Description("Sets an alarm at the provided time")]
    public string SetAlarm(string time)
    {
        this.hour = time;
        return GetCurrentAlarm();
    }

    [KernelFunction, Description("Get current alarm set")]
    public string GetCurrentAlarm()
    {
        return $"Alarm set for {hour}";
    }
}
