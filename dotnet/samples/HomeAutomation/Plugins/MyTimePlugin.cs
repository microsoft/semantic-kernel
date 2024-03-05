// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using Microsoft.SemanticKernel;

namespace HomeAutomation.Plugins;

/// <summary>
/// Simple plugin that just returns the time.
/// </summary>
public class MyTimePlugin
{
    [KernelFunction, Description("Get the current time")]
    public DateTimeOffset Time() => DateTimeOffset.Now;
}
