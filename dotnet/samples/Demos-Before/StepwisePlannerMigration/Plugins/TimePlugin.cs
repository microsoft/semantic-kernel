// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using Microsoft.SemanticKernel;

namespace StepwisePlannerMigration.Plugins;

/// <summary>
/// Sample plugin which provides time information.
/// </summary>
public sealed class TimePlugin
{
    [KernelFunction]
    [Description("Retrieves the current time in UTC")]
    public string GetCurrentUtcTime() => DateTime.UtcNow.ToString("R");
}
