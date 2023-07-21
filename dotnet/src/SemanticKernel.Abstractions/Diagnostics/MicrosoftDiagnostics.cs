// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Diagnostics;

public static class MicrosoftDiagnostics
{
    /// <summary>
    /// Env var used in Azure to enable/disable telemetry
    /// </summary>
    private const string TelemetryDisabledEnvVar = "AZURE_TELEMETRY_DISABLED";

    /// <summary>
    /// HTTP User Agent
    /// Note: Azure max length 24 chars
    /// </summary>
    public const string HttpUserAgent = "Semantic-Kernel";

    /// <summary>
    /// Source: https://github.com/Azure/azure-sdk-for-net/blob/main/sdk/core/Azure.Core/src/DiagnosticsOptions.cs
    /// </summary>
    public static bool IsTelemetryEnabled => !EnvVarToBool(Environment.GetEnvironmentVariable(TelemetryDisabledEnvVar)) ?? true;

    /// <summary>
    /// Source: https://github.com/Azure/azure-sdk-for-net/blob/main/sdk/core/Azure.Core/src/DiagnosticsOptions.cs
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
