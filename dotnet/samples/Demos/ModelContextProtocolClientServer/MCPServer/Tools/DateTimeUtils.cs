// Copyright (c) Microsoft. All rights reserved.

using System.ComponentModel;
using Microsoft.SemanticKernel;

namespace MCPServer.Tools;

/// <summary>
/// A collection of utility methods for working with date time.
/// </summary>
internal sealed class DateTimeUtils
{
    /// <summary>
    /// Retrieves the current date time in UTC.
    /// </summary>
    /// <returns>The current date time in UTC.</returns>
    [KernelFunction, Description("Retrieves the current date time in UTC.")]
    public static string GetCurrentDateTimeInUtc()
    {
        return DateTime.UtcNow.ToString("yyyy-MM-dd HH:mm:ss");
    }
}
