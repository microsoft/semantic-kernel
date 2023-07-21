// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Diagnostics;

public static class Telemetry
{
    /// <summary>
    /// Env var used in Azure to enable/disable telemetry
    /// See: https://learn.microsoft.com/en-us/dotnet/api/azure.core.diagnosticsoptions.istelemetryenabled?view=azure-dotnet
    /// </summary>
    private const string TelemetryDisabledEnvVar = "AZURE_TELEMETRY_DISABLED";

    /// <summary>
    /// HTTP User Agent
    /// Note: Azure max length 24 chars
    /// </summary>
    public const string HttpUserAgent = "Semantic-Kernel";

    /// <summary>
    /// Source: https://github.com/Azure/azure-sdk-for-net/blob/main/sdk/core/Azure.Core/src/DiagnosticsOptions.cs
    /// Azure customers setting AZURE_TELEMETRY_DISABLED=1 expect telemetry to be disabled.
    /// </summary>
    public static bool IsTelemetryEnabled => !EnvExtensions.GetBoolEnvVar(TelemetryDisabledEnvVar) ?? true;

    /// <summary>
    /// Source: https://github.com/Azure/azure-sdk-for-net/blob/main/sdk/core/Azure.Core/src/DiagnosticsOptions.cs
    /// Values: https://learn.microsoft.com/en-us/dotnet/api/azure.core.diagnosticsoptions.istelemetryenabled?view=azure-dotnet
    /// </summary>
    private static bool? EnvVarToBool(string? value)
    {
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
