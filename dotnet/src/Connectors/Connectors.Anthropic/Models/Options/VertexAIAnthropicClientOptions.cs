// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Connectors.Anthropic;

/// <summary>
/// Represents the options for configuring the Anthropic client with Google VertexAI provider.
/// </summary>
public sealed class VertexAIAnthropicClientOptions : ClientOptions
{
    private const ServiceVersion LatestVersion = ServiceVersion.V2023_10_16;

    /// <summary> The version of the service to use. </summary>
    public enum ServiceVersion
    {
        /// <summary> Service version "vertex-2023-10-16". </summary>
        V2023_10_16,
    }

    /// <summary>
    /// Initializes new instance of <see cref="VertexAIAnthropicClientOptions"/>
    /// </summary>
    /// <param name="version">
    /// This parameter is optional.
    /// Default value is <see cref="VertexAIAnthropicClientOptions.LatestVersion"/>.<br/>
    /// </param>
    /// <exception cref="NotSupportedException">Provided version is not supported.</exception>
    public VertexAIAnthropicClientOptions(ServiceVersion version = LatestVersion) : base(version switch
    {
        ServiceVersion.V2023_10_16 => "vertex-2023-10-16",
        _ => throw new NotSupportedException("Unsupported service version")
    })
    {
    }
}
