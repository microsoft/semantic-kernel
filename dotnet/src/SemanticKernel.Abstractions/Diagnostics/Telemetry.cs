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
}
