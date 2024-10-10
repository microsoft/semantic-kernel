// Copyright (c) Microsoft. All rights reserved.

using System;

namespace Microsoft.SemanticKernel.Connectors.Anthropic;

/// <summary>
/// Represents the options for configuring the Anthropic client with Amazon Bedrock provider.
/// </summary>
public sealed class AmazonBedrockAnthropicClientOptions : ClientOptions
{
    private const ServiceVersion LatestVersion = ServiceVersion.V2023_05_31;

    /// <summary> The version of the service to use. </summary>
    public enum ServiceVersion
    {
        /// <summary> Service version "bedrock-2023-05-31". </summary>
        V2023_05_31,
    }

    /// <summary>
    /// Initializes new instance of <see cref="AmazonBedrockAnthropicClientOptions"/>
    /// </summary>
    /// <param name="version">
    /// This parameter is optional.
    /// Default value is <see cref="AmazonBedrockAnthropicClientOptions.LatestVersion"/>.<br/>
    /// </param>
    /// <exception cref="NotSupportedException">Provided version is not supported.</exception>
    public AmazonBedrockAnthropicClientOptions(ServiceVersion version = LatestVersion) : base(version switch
    {
        ServiceVersion.V2023_05_31 => "bedrock-2023-05-31",
        _ => throw new NotSupportedException("Unsupported service version")
    })
    {
    }
}
