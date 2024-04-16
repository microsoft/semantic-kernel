// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Connectors.Anthropic;

#pragma warning disable CA1707 // Identifiers should not contain underscores

/// <summary>
/// Represents the options for configuring the Anthropic client.
/// </summary>
public sealed class AnthropicClientOptions
{
    private const ServiceVersion LatestVersion = ServiceVersion.V2023_06_01;

    /// <summary> The version of the service to use. </summary>
#pragma warning disable CA1008 // Enums should have zero value
    public enum ServiceVersion
#pragma warning restore CA1008
    {
        /// <summary> Service version "2023-01-01". </summary>
        V2023_01_01 = 1,

        /// <summary> Service version "2023-06-01". </summary>
        V2023_06_01 = 2,
    }

    internal string Version { get; }

    /// <summary> Initializes new instance of OpenAIClientOptions. </summary>
    public AnthropicClientOptions(ServiceVersion version = LatestVersion)
    {
        this.Version = version switch
        {
            ServiceVersion.V2023_01_01 => "2023-01-01",
            ServiceVersion.V2023_06_01 => "2023-06-01",
            _ => throw new NotSupportedException("Unsupported service version")
        };
    }
}
