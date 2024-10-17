// Copyright (c) Microsoft. All rights reserved.

#pragma warning disable IDE0005 // Using directive is unnecessary

using System;
using System.ComponentModel;
using Microsoft.SemanticKernel;

#pragma warning restore IDE0005 // Using directive is unnecessary

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
