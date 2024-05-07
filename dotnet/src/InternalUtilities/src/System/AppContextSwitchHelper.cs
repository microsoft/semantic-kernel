// Copyright (c) Microsoft. All rights reserved.

using System;
using System.Diagnostics.CodeAnalysis;

namespace Microsoft.SemanticKernel;

/// <summary>
/// Helper class to get app context switch value
/// </summary>
[ExcludeFromCodeCoverage]
internal static class AppContextSwitchHelper
{
    /// <summary>
    /// Get app context switch value.
    /// If the switch is not set, return false.
    /// </summary>
    public static bool GetConfigValue(string appContextSwitchName)
    {
        if (AppContext.TryGetSwitch(appContextSwitchName, out bool value))
        {
            return value;
        }

        return false;
    }
}
