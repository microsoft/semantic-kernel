// Copyright (c) Microsoft. All rights reserved.

namespace System;

internal static class EnvExtensions
{
    /// <summary>
    /// Source: https://github.com/Azure/azure-sdk-for-net/blob/main/sdk/core/Azure.Core/src/DiagnosticsOptions.cs
    /// Values: https://learn.microsoft.com/en-us/dotnet/api/azure.core.diagnosticsoptions.istelemetryenabled?view=azure-dotnet
    /// </summary>
    internal static bool? GetBoolEnvVar(string name)
    {
        string? value = Environment.GetEnvironmentVariable(name);

        if (string.Equals(bool.TrueString, value, StringComparison.OrdinalIgnoreCase) ||
            string.Equals("1", value, StringComparison.OrdinalIgnoreCase))
        {
            return true;
        }

        if (string.Equals(bool.FalseString, value, StringComparison.OrdinalIgnoreCase) ||
            string.Equals("0", value, StringComparison.OrdinalIgnoreCase))
        {
            return false;
        }

        return null;
    }
}
